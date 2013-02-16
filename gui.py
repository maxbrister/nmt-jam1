import cairo
import math
import numpy
import pango
import pangocairo
import re

from panda3d.core import CardMaker, CPTA_uchar, PTA_uchar, Texture, TextureStage, TransformState, VBase2, VBase4, Vec2, TransparencyAttrib, RenderAttrib

_COLOR_RE = re.compile('^#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})?$')
def toColor(clr):
    try:
        match = _COLOR_RE.match(clr)
        if match:
            tmp = [match.group(idx) for idx in xrange(1, 5)]
            return [int(v, 16)/255.0 if v else 1.0 for v in tmp]
    except TypeError:
        if len(clr) == 4:
            return [float(v) for v in clr]
        raise TypeError('Can not convert ' + str(clr) + ' to a color')

def toOrient(o):
    if o in ['left', 'top']:
        return 0
    if o in ['right', 'bottom']:
        return 1
    if o == 'center':
        return .5
    return int(o)

def _allSame(v):
    if len(v) <= 1:
        return True
    return all([v[0] == item for item in v])

def _makeList(v, le):
    if isinstance(v, str):
        split = v.split(' ')
        if len(split) == le:
            return split
    else:
        try:
            lenv = len(v)
        except TypeError:
            lenv = -1
                
        if lenv == le:
            return v
            
    return [v for _ in xrange(le)]
            
class PropertySet(object):
    def __init__(self, id = '', parent=None):
        self.id = id
        self._parent = None
        self.parent= parent
        self._props = dict()
        self._classes = list()
        self._children = list()
        self._listeners = dict()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, p):
        self._setParent(p)

    def __getitem__(self, name):
        return self.getProperty(name).value

    def __setitem__(self, name, v):
        try:
            self._props[name].value = v
        except KeyError:
            prop = self.addProperty(name)
            prop.value = v

    def addClass(self, cl):
        self.removeClass(cl)
        self._classes.append(cl)

        # We must have all properties in the class
        fakes = list()
        for pname in cl._props:
            if pname not in self._props:
                prop = cl._props[pname]
                if isinstance(_FakeProperty, prop):
                    fakes.append(prop)
                else:
                    self._props[pname] = cl._props[pname].clone(self)
        for fake in fakes:
            self._props[fake.name] = fake.clone(self)

    def addCompositeProperty(self, name, names, defaultValue=None, convertFn=None, defaultInherit=False):
        defaultValue = _makeList(defaultValue, len(names))
        convertFn = _makeList(convertFn, len(names))
        props = [self.addProperty(pname, dv, cf, defaultInherit) for pname, cf, dv in
                 zip(names, convertFn, defaultValue)]
        ret = _FakeProperty(self, name, props)
        self._props[name] = ret
        return ret

    def addListener(self, evt, l):
        try:
            self._listeners[evt].append(l)
        except KeyError:
            self._listeners[evt] = [l]
        return l

    def addProperty(self, name, defaultValue=None, convertFn=None, defaultInherit=False):
        ret = _Property(self, name, defaultValue, convertFn, defaultInherit)
        self._props[name] = ret
        self._updateInherit(name, self._parent[name] if self._parent else None)
        return ret

    def addRectProperty(self, name, defaultValue=None, convertFn=None, defaultInherit=False):
        self.addCompositeProperty(name, [name + ext for ext in ['Left', 'Top', 'Right', 'Bottom']],
                                  defaultValue, convertFn, defaultInherit)

    def getProperty(self, name):
        try:
            return self._props[name]
        except KeyError:
            prop = self.addProperty(name)
            return prop

    def removeClass(self, cl):
        for idx, c in enumerate(self._classes):
            if c.name == cl.name:
                del self._classes[idx]
                break
        self._markAllDirty()

    def removeListener(self, evt, l):
        self._listeners[evt].remove(l)

    def _sendEvent(self, evt, oldValue, newValue):
        try:
            lsts = self._listeners[evt]
        except KeyError:
            return

        for listener in lsts:
            listener(evt, oldValue, newValue)

    def _setParent(self, p):
        if p != self._parent:
            if self._parent is not None:
                self._parent._removeChild(self)
            self._parent = p
            if self._parent is not None:
                self._parent._addChild(self)
            self._updateInheritAll()
            return True
        return False

    def _update(self, pname):
        if self.getProperty(pname)._update():
            for c in self._children:
                c._updateInherit(pname, prop.value)

    def _updateInherit(self, pname, pvalue):
        try:
            prop = self._props[pname]
            if not prop._updateInherit(pvalue):
                return
            value = prop.value
        except KeyError:
            value = pvalue

        for c in self._children:
            c._updateInherit(pname, value)

    def _updateInheritAll(self):
        if self._parent:
            for nm in self._parent._props:
                self._updateInherit(nm, self._parent[nm])
                
        for nm in self._props:
            if not self._parent or nm not in self._parent._props:
                self._updateInherit(nm, None)

class Component(PropertySet):
    def __init__(self, id = '', parent = None):
        super(Component, self).__init__(id, parent)

        self._context = None
        self._pangoContext = None

        self.addProperty('width', 0, float)
        self.addProperty('height', 0, float)
        self.addProperty('minWidth', 0, float)
        self.addProperty('minHeight', 0, float)
        self.addProperty('maxWidth', float('inf'), float)
        self.addProperty('maxHeight', float('inf'), float)
        self.addRectProperty('margin', 0, float)
        self.addRectProperty('padding', 0, float)
        self.addRectProperty('border', 0, float)
        self.addProperty('borderColor', '#000000', toColor)
        self.addProperty('horizontalAlign', 'left', toOrient)
        self.addProperty('verticalAlign', 'right', toOrient)

        self._sizeValid = False
        self.position = None
        self.size = None

    def computeSize(self):
        # DO NOT override
        csize = self._computeContentSize()
        space = [self['margin'], self['padding'], self['border']]
        space = [(s[:2], s[2:]) for s in space]
        s0, s1 = zip(*space)
        xspace, yspace = zip(*(s0 + s1))
        return csize[0] + sum(xspace), csize[1] + sum(yspace)

    def render(self, size):
        # DO NOT override
        margin = self['margin']
        padding = self['padding']
        border = self['border']

        ctx = self._context
        ctx.save()
        ctx.rectangle(0, 0, *size)
        ctx.clip()
        ctx.translate(*margin[:2])

        size = Vec2(*size)
        size -= Vec2(*margin[:2])
        size -= Vec2(*margin[2:])

        # draw the border
        ctx.save()
        ctx.set_source_rgba(*self['borderColor'])
        if _allSame(border):
            border = border[0]
            if border > 0:
                ctx.set_line_width(border)
                ctx.rectangle(0, 0, size[0], size[1])
                ctx.translate(border, border)
                size -= Vec2(border, border) * 2
        else:
            raise Exception('Not supported yet')
        ctx.restore()

        # take into account the padding
        size -= Vec2(*padding[:2])
        size -= Vec2(*padding[:2])

        self._renderContent(size)
        
        ctx.restore()

    def _computeContentSize(self):
        # subclass should override
        return (0, 0)

    def _updateContext(self, ctx, pangoCtx):
        self._context = ctx
        self._pangoContext = pangoCtx
        for c in self._children:
            c._updateContext(ctx, pangoCtx)

    def _invalidateSize(self):
        if self._sizeValid and self.parent is not None:
            self._sizeValid = False
            self.parent._childInvalidateSize(self)

    def _renderContent(self, size):
        # subclass should override
        pass

    def _setParent(self, p):
        if super(Component, self)._setParent(p):
            if p:
                self._updateContext(p._context, p._pangoContext)
            else:
                self._updateContext(None, None)

    def _updateLayout(self, size):
        # subclass should override
        pass

class Container(Component):
    def __init__(self, id = '', parent = None):
        super(Container, self).__init__(id, parent)

    def addChild(self, c):
        c.parent = self

    def removeChild(self, c):
        c.parent = None

    def _addChild(self, c):
        self._children.append(c)
        self._invalidateSize()

    def _removeChild(self, c):
        self._children.remove(c)
        self._invalidateSize()

    def _renderContent(self, size):
        ctx = self._context
        for c in self._children:
            ctx.save()
            ctx.translate(*c.position)
            c.render(c.size)
            ctx.restore()

class Box(Container):
    def __init__(self, id = '', parent = None):
        super(Box, self).__init__(id, parent)
        self.addProperty('orientation', 'horizontal')
        self.addProperty('spacing', 5, int)
        self.addProperty('verticalAlign', 'center', toOrient)
        self.addProperty('horizontalAlign', 'center', toOrient)

    @property
    def _idx0(self):
        return 0 if self['orientation'] == 'horizontal' else 1

    @property
    def _idx1(self):
        return (self._idx0 + 1) % 2

    @property
    def _orient0(self):
        return self['horizontalAlign'] if self['orientation'] == 'horizontal' else self['verticalAlign']

    @property
    def _orient1(self):
        return self['verticalAlign'] if self['orientation'] == 'horizontal' else self['horizontalAlign']

    def _computeContentSize(self):
        size = [0, 0]
        for c in self._children:
            s = c.computeContentSize()
            size[self._idx0] += s[self._idx0]
            size[self._idx1] = max(size[self._idx1], s[self._idx1])

        spacing = self['spacing']
        size[self._idx0] += (len(self._children) - 1) * spacing
        return size

    def _updateLayout(self, size):
        pos = [0, 0]
        spacing = self['spacing']
        for c in self._children:
            c.size = c.computeSize()
            c.position = list(pos)
            diff = size[self._idx1] - c.size[self._idx1]
            if diff > 0:
                c.position[self._idx1] += self._orient1 * diff
                            
            pos[self._idx0] += pos[self._idx0] + spacing

        diff = size[self._idx0] - pos[self._idx0]
        if diff > 0:
            offset = diff * self._orient0
            for c in self._children:
                c.position[self._idx0] += offset

class HBox(Box):
    def __init__(self, id = '', parent = None):
        super(HBox, self).__init__(id, parent)

class VBox(Box):
    def __init__(self, id = '', parent = None):
        super(VBox, self).__init__(id, parent)
        self.getProperty('orientation').defaultValue = 'vertical'

class Text(Component):
    def __init__(self, id = '', parent = None):
        super(Text, self).__init__(id, parent)
        self.addProperty('text', '', str)
        self.addProperty('fontSize', 16, int, defaultInherit=True)
        self.addProperty('fontName', 'Sans', str)
        self.addProperty('fontColor', '#00FF00', toColor, defaultInherit=True)
        self._layout = None

    def _computeContentSize(self):
        layout = self._genLayout()
        return [s / pango.SCALE for s in layout.get_size()]

    def _genLayout(self):
        pctx = self._pangoContext
        if self._layout is None:
            self._layout = pctx.create_layout()
            self._layout.set_width(-1)

        font = pango.FontDescription('{0} {1}'.format(self['fontName'], self['fontSize']))
        self._layout.set_font_description(font)

        if self._layout.get_text() != self['text']:
            self._layout.set_text(self['text'])
            pctx.update_layout(self._layout)
            
        return self._layout

    def _renderContent(self, size):
        self._context.set_source_rgb(1, 0, 0)
        layout = self._genLayout()
        self._pangoContext.show_layout(layout)

    def _updateContext(self, context, pangoContext):
        self._layout = None
        super(Text, self)._updateContext(context, pangoContext)

class Manager(Box):
    def __init__(self, visible=True):
        super(Manager, self).__init__()
        
        self._size = None
        cm = CardMaker('card')
        cm.setFrame(-1, 1, 1, -.5)
        self._card = render2d.attachNewNode(cm.generate())
        self._card.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MAlpha))
        self._card.hide()

        self._visible = False
        self.visible = visible

        self.content = None

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        if v != self._visible:
            self._visible = v
            if v:
                self._task = base.taskMgr.add(self.render, 'render-gui')
                self._card.show()
            else:
                base.taskMgr.remove(self._task)
                self._task = None
                self._card.hide()

    def render(self, task):
        size = self.resize()
        ctx = self._context
        ctx.save()
        ctx.set_source_rgba(0, 0, 0, 0)
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.paint()
        ctx.restore()

        super(Manager, self).render(self._size)

        self._buffer.setData(self._surface.get_data())
        self._tex.setRamImage(CPTA_uchar(self._buffer), Texture.CMOff)
        return True

    def resize(self, size=None):
        props = base.win.getProperties()
        size = props.getXSize(), props.getYSize()
        if self._size == size:
            return size

        self._size = size
        self._data = numpy.empty(size[0] * size[1] * 4, dtype=numpy.int8)
        self._surface = cairo.ImageSurface.create_for_data(self._data, cairo.FORMAT_ARGB32,
                                                           size[0], size[1], size[0] * 4)
        self._buffer = PTA_uchar.emptyArray(self._size[0] * self._size[1] * 4)
        
        self._tex = Texture()
        self._tex.setup2dTexture(self._size[0], self._size[1], Texture.TUnsignedByte, Texture.FRgba)
        self._tex.setMagfilter(Texture.FTNearest)
        self._tex.setMinfilter(Texture.FTNearest)
        self._card.setTexture(self._tex)

        context = cairo.Context(self._surface)
        pangoContext = pangocairo.CairoContext(context)
        self._updateContext(context, pangoContext)
        self._updateLayout(size)
        return size

class _FakeProperty(object):
    def __init__(self, ps, name, props):
        self._pset = ps

        self._name = name
        self._props = props
        self._defaultInherit = all([prop.defaultInherit for prop in props])
        
    @property
    def defaultValue(self):
        return tuple([prop.defaultValue for prop in self._props])

    @defaultValue.setter
    def defaultValue(self, v):
        for prop, dv in zip(self._props, self._parse(v)):
            prop.defaultValue = dv

    @property
    def inherit(self):
        return all([prop.inherit for prop in self._props])

    @inherit.setter
    def inherit(self, v):
        for prop in self._props:
            prop.inherit = v

    @property
    def value(self):
        return [prop.value for prop in self._props]

    @value.setter
    def value(self, v):
        for prop, v in zip(self._props, self._parse(v)):
            prop.value = v

    @property
    def name(self):
        return self._name

    def clone(self, pset):
        return _FakeProperty(pset, self.name, [prop.name for prop in self._props])

    def _parse(self, v):
        return _makeList(v, len(self._props))

    def _update(self):
        return False

    def _updateInherit(self, pvalue):
        return False
        
class _Property(object):
    def __init__(self, ps, name, defaultValue, convertFn, defaultInherit):
        self._pset = ps
        
        self._name = name
        self._defaultValue = defaultValue
        self._convertFn = convertFn
        self._defaultInherit = None

        self._inheritValue = None
        self._value = None
        self._inherit = None
        
        self._computedValue = None

    @property
    def defaultInherit(self):
        return self._defaultInherit

    @defaultInherit.setter
    def defaultInherit(self, v):
        self._defaultInherit = v
        self.markDirty()

    @property
    def defaultValue(self):
        return self._defaultValue

    @defaultValue.setter
    def defaultValue(self, v):
        self._defaultValue = v
        self.markDirty()

    @property
    def inherit(self):
        return self._defaultInherit if self._inherit is None else self._inherit

    @inherit.setter
    def inhert(self, v):
        if self._inherit != v:
            self._inherit = v
            self.markDirty()

    @property
    def value(self):
        return self._computedValue

    @value.setter
    def value(self, v):
        if self._value != v:
            self._value = v
            self.markDirty()

    @property
    def name(self):
        return self._name

    def clone(self, pset):
        return _Property(pset, self.name, self._defaultValue, self._convertFn, self._defaultInherit)

    def markDirty(self):
        self._pset._update(self.name)

    def _update(self):
        if self._value is not None:
            newValue = self._value
        elif self.inherit and self._inheritValue is not None:
            newValue = self._inheritValue
        else:
            newValue = self._defaultValue

        try:
            newValue = newValue()
        except TypeError:
            pass

        if self._convertFn is not None:
            newValue = self._convertFn(newValue)

        if newValue != self._computedValue:
            oldValue = self._computedValue
            self._computedValue = newValue
            self._pset._sendEvent(self.name, oldValue, newValue)
            return True
        return False

    def _updateInherit(self, pvalue):
        self._inheritValue = pvalue
        return self._update()

if __name__ == '__main__':
    import direct.directbase.DirectStart

    base.win.setClearColorActive(True)
    base.win.setClearColor(VBase4(0, 0, 1, 1))
    mgr = Manager()

    txt = Text()
    txt['text'] = 'hello world'
    txt.parent = mgr
    run()
