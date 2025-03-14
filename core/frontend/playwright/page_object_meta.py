class PageObjectMeta(type):
    def __new__(mcs, name, bases, attrs):
        # Creating the class
        cls = super().__new__(mcs, name, bases, attrs)

        # Adding a method to initialize elements
        original_init = cls.__init__

        def __init_with_elements__(self, *args, **kwargs):
            # Call the original __init__
            original_init(self, *args, **kwargs)

            # Initialize elements after instance creation
            if hasattr(self, '_page') and self._page is not None:
                for attr_name in dir(self):
                    attr = getattr(self, attr_name)
                    from core.frontend.playwright.elements.ui_element import UIElement
                    if isinstance(attr, UIElement) and getattr(attr, '_page', None) is None:
                        attr.set_page(self._page)

        cls.__init__ = __init_with_elements__
        return cls
