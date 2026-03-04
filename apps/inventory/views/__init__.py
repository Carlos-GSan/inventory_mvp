from .dashboard import dashboard  # noqa: F401
from .inventory import (  # noqa: F401
    inventory_list,
    inventory_create,
    inventory_update,
    inventory_adjust,
    inventory_print_label,
    inventory_print_labels,
)
from .purchases import (  # noqa: F401
    purchase_list,
    purchase_create,
    purchase_detail,
    purchase_update,
    purchase_delete,
)
from .requisitions import (  # noqa: F401
    requisition_list,
    requisition_create,
    requisition_detail,
)
from .suppliers import supplier_list, supplier_create, supplier_update  # noqa: F401
from .categories import category_list, category_create, category_update  # noqa: F401
from .photos import item_photo_delete, purchase_photo_delete  # noqa: F401
