from pydoctor.test.test_astbuilder import fromText
from pydoctor.test.test_packages import processPackage
from pydoctor.zopeinterface import ZopeInterfaceSystem

# we set up the same situation using both implements and
# classImplements and run the same tests.

def test_implements():
    src = '''
    import zope.interface

    class IFoo(zope.interface.Interface):
        pass
    class IBar(zope.interface.Interface):
        pass

    class Foo:
        zope.interface.implements(IFoo)
    class FooBar(Foo):
        zope.interface.implements(IBar)
    class OnlyBar(Foo):
        zope.interface.implementsOnly(IBar)
    '''
    implements_test(src)

def test_classImplements():
    src = '''
    import zope.interface
    class IFoo(zope.interface.Interface):
        pass
    class IBar(zope.interface.Interface):
        pass
    class Foo:
        pass
    class FooBar(Foo):
        pass
    class OnlyBar(Foo):
        pass
    zope.interface.classImplements(Foo, IFoo)
    zope.interface.classImplements(FooBar, IBar)
    zope.interface.classImplementsOnly(OnlyBar, IBar)
    '''
    implements_test(src)

def test_implementer():
    src = '''
    import zope.interface

    class IFoo(zope.interface.Interface):
        pass
    class IBar(zope.interface.Interface):
        pass

    @zope.interface.implementer(IFoo)
    class Foo:
        pass
    @zope.interface.implementer(IBar)
    class FooBar(Foo):
        pass
    class OnlyBar(Foo):
        zope.interface.implementsOnly(IBar)
    '''
    implements_test(src)

def implements_test(src):
    mod = fromText(src, 'zi', systemcls=ZopeInterfaceSystem)
    ifoo = mod.contents['IFoo']
    ibar = mod.contents['IBar']
    foo = mod.contents['Foo']
    foobar = mod.contents['FooBar']
    onlybar = mod.contents['OnlyBar']

    assert ifoo.isinterface and ibar.isinterface
    assert not foo.isinterface and not foobar.isinterface and not foobar.isinterface

    assert not foo.implementsOnly and not foobar.implementsOnly
    assert onlybar.implementsOnly

    assert foo.implements_directly == ['zi.IFoo']
    assert foo.allImplementedInterfaces == ['zi.IFoo']
    assert foobar.implements_directly == ['zi.IBar']
    assert foobar.allImplementedInterfaces == ['zi.IBar', 'zi.IFoo']
    assert onlybar.implements_directly == ['zi.IBar']
    assert onlybar.allImplementedInterfaces == ['zi.IBar']

    assert ifoo.implementedby_directly == [foo]
    assert ifoo.allImplementations == [foo, foobar]
    assert ibar.implementedby_directly == [foobar, onlybar]
    assert ibar.allImplementations == [foobar, onlybar]


def test_subclass_with_same_name():
    src = '''
    class A:
        pass
    class A(A):
        pass
    '''
    fromText(src, 'zi', systemcls=ZopeInterfaceSystem)

def test_multiply_inheriting_interfaces():
    src = '''
    from zope.interface import Interface, implements

    class IOne(Interface): pass
    class ITwo(Interface): pass
    class One: implements(IOne)
    class Two: implements(ITwo)
    class Both(One, Two): pass
    '''
    mod = fromText(src, 'zi', systemcls=ZopeInterfaceSystem)
    assert len(mod.contents['Both'].allImplementedInterfaces) == 2

def test_attribute(capsys):
    src = '''
    import zope.interface as zi
    class C(zi.Interface):
        attr = zi.Attribute("documented attribute")
        bad_attr = zi.Attribute(0)
    '''
    mod = fromText(src, modname='mod', systemcls=ZopeInterfaceSystem)
    assert len(mod.contents['C'].contents) == 2
    attr = mod.contents['C'].contents['attr']
    assert attr.kind == 'Attribute'
    assert attr.name == 'attr'
    assert attr.docstring == "documented attribute"
    bad_attr = mod.contents['C'].contents['bad_attr']
    assert bad_attr.kind == 'Attribute'
    assert bad_attr.name == 'bad_attr'
    assert bad_attr.docstring is None
    captured = capsys.readouterr().out
    assert captured == 'mod:5: definition of attribute "bad_attr" should have docstring as its sole argument\n'

def test_interfaceclass():
    system = processPackage('interfaceclass', systemcls=ZopeInterfaceSystem)
    mod = system.allobjects['interfaceclass.mod']
    assert mod.contents['MyInterface'].isinterface
    assert mod.contents['MyInterface'].docstring == "This is my interface."
    assert mod.contents['AnInterface'].isinterface

def test_warnerproofing():
    src = '''
    from zope import interface
    Interface = interface.Interface
    class IMyInterface(Interface):
        pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    assert mod.contents['IMyInterface'].isinterface

def test_zopeschema(capsys):
    src = '''
    from zope import schema, interface
    class IMyInterface(interface.Interface):
        text = schema.TextLine(description="fun in a bun")
        undoc = schema.Bool()
        bad = schema.ASCII(description=False)
    '''
    mod = fromText(src, modname='mod', systemcls=ZopeInterfaceSystem)
    text = mod.contents['IMyInterface'].contents['text']
    assert text.docstring == 'fun in a bun'
    assert text.kind == "TextLine"
    undoc = mod.contents['IMyInterface'].contents['undoc']
    assert undoc.docstring is None
    assert undoc.kind == "Bool"
    bad = mod.contents['IMyInterface'].contents['bad']
    assert bad.docstring is None
    assert bad.kind == "ASCII"
    captured = capsys.readouterr().out
    assert captured == 'mod:6: description of field "bad" is not a string literal\n'

def test_aliasing_in_class():
    src = '''
    from zope import interface
    class IMyInterface(interface.Interface):
        Attrib = interface.Attribute
        attribute = Attrib("fun in a bun")
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    attr = mod.contents['IMyInterface'].contents['attribute']
    assert attr.docstring == 'fun in a bun'
    assert attr.kind == "Attribute"

def test_zopeschema_inheritance():
    src = '''
    from zope import schema, interface
    from zope.schema import Int as INTEGERSCHMEMAFIELD
    class MyTextLine(schema.TextLine):
        pass
    class MyOtherTextLine(MyTextLine):
        pass
    class IMyInterface(interface.Interface):
        mytext = MyTextLine(description="fun in a bun")
        myothertext = MyOtherTextLine(description="fun in another bun")
        myint = INTEGERSCHMEMAFIELD(description="not as much fun")
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    mytext = mod.contents['IMyInterface'].contents['mytext']
    assert mytext.docstring == 'fun in a bun'
    assert mytext.kind == "MyTextLine"
    myothertext = mod.contents['IMyInterface'].contents['myothertext']
    assert myothertext.docstring == 'fun in another bun'
    assert myothertext.kind == "MyOtherTextLine"
    myint = mod.contents['IMyInterface'].contents['myint']
    assert myint.kind == "Int"

def test_docsources_includes_interface():
    src = '''
    from zope import interface
    class IInterface(interface.Interface):
        def method(self):
            """documentation"""
    class Implementation:
        interface.implements(IInterface)
        def method(self):
            pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    imethod = mod.contents['IInterface'].contents['method']
    method = mod.contents['Implementation'].contents['method']
    assert imethod in method.docsources(), list(method.docsources())

def test_docsources_includes_baseinterface():
    src = '''
    from zope import interface
    class IBase(interface.Interface):
        def method(self):
            """documentation"""
    class IExtended(IBase):
        pass
    class Implementation:
        interface.implements(IExtended)
        def method(self):
            pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    imethod = mod.contents['IBase'].contents['method']
    method = mod.contents['Implementation'].contents['method']
    assert imethod in method.docsources(), list(method.docsources())

def test_docsources_interface_attribute():
    src = '''
    from zope import interface
    class IInterface(interface.Interface):
        attr = interface.Attribute("""documentation""")
    @interface.implementer(IInterface)
    class Implementation:
        attr = True
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    iattr = mod.contents['IInterface'].contents['attr']
    attr = mod.contents['Implementation'].contents['attr']
    assert iattr in list(attr.docsources())

def test_implementer_decoration():
    src = '''
    from zope.interface import Interface, implementer
    class IMyInterface(Interface):
        def method(self):
            """documentation"""
    @implementer(IMyInterface)
    class Implementation:
        def method(self):
            pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    iface = mod.contents['IMyInterface']
    impl = mod.contents['Implementation']
    assert impl.implements_directly == [iface.fullName()]

def test_implementer_decoration_nonclass():
    src = '''
    from zope.interface import implementer
    var = 0
    @implementer(var)
    class Implementation:
        pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    impl = mod.contents['Implementation']
    assert impl.implements_directly == []

def test_docsources_from_moduleprovides():
    src = '''
    from zope import interface

    class IBase(interface.Interface):
        def bar():
            """documentation"""

    interface.moduleProvides(IBase)

    def bar():
        pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    imethod = mod.contents['IBase'].contents['bar']
    function = mod.contents['bar']
    assert imethod in function.docsources(), list(function.docsources())

def test_interfaceallgames():
    system = processPackage('interfaceallgames', systemcls=ZopeInterfaceSystem)
    mod = system.allobjects['interfaceallgames.interface']
    assert [o.fullName() for o in mod.contents['IAnInterface'].allImplementations] == ['interfaceallgames.implementation.Implementation']

def test_implementer_with_none():
    """
    If the implementer call contains a split out empty list, don't fail on
    attempting to process it.
    """
    src = '''
    from zope.interface import Interface, implementer
    extra_interfaces = ()
    class IMyInterface(Interface):
        def method(self):
            """documentation"""
    @implementer(IMyInterface, *extra_interfaces)
    class Implementation:
        def method(self):
            pass
    '''
    mod = fromText(src, systemcls=ZopeInterfaceSystem)
    iface = mod.contents['IMyInterface']
    impl = mod.contents['Implementation']
    assert impl.implements_directly == [iface.fullName()]

def test_implementer_nonclass(capsys):
    """
    Check rejection of non-class arguments passed to @implementer.
    """
    src = '''
    from zope.interface import Interface, implementer
    var = 'not a class'
    @implementer(var)
    class Implementation:
        pass
    '''
    mod = fromText(src, modname='mod', systemcls=ZopeInterfaceSystem)
    impl = mod.contents['Implementation']
    assert impl.implements_directly == []
    captured = capsys.readouterr().out
    assert captured == "mod:4: probable interface mod.var not detected as a class\n"

def test_implementer_plainclass(capsys):
    """
    Check patching of non-interface classes passed to @implementer.
    """
    src = '''
    from zope.interface import Interface, implementer
    class C:
        pass
    @implementer(C)
    class Implementation:
        pass
    '''
    mod = fromText(src, modname='mod', systemcls=ZopeInterfaceSystem)
    C = mod.contents['C']
    impl = mod.contents['Implementation']
    assert C.isinterface
    assert C.kind == "Interface"
    assert C.implementedby_directly == [impl]
    assert impl.implements_directly == ['mod.C']
    captured = capsys.readouterr().out
    assert captured == "mod:5: probable interface mod.C not marked as such\n"
