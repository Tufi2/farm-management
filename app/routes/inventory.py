from flask import Blueprint

bp = Blueprint('inventory', __name__)

@bp.route('/inventory')
def inventory_list():
    return "Inventory List"