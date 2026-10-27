# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.fields import Domain
from odoo.orm.domains import (
    DomainAnd,
    DomainBool,
    DomainCondition,
    DomainNary,
    DomainNot,
)


def _extract_location_domain(domain):
    """Return the conditions of a quant domain on its location, for the locations.

    The conditions on other fields of the quant are removed, along with the
    operators left without operands. Return ``None`` when no condition is left.
    """
    if isinstance(domain, DomainBool):
        return domain
    if isinstance(domain, DomainNary):
        children = [
            child
            for child in map(_extract_location_domain, domain.children)
            if child is not None
        ]
        if not children:
            return None
        if isinstance(domain, DomainAnd):
            return Domain.AND(children)
        return Domain.OR(children)
    if isinstance(domain, DomainNot):
        child = _extract_location_domain(domain.child)
        return None if child is None else ~child
    if isinstance(domain, DomainCondition):
        field_expr = domain.field_expr
        if field_expr == "location_id":
            if domain.operator == "any":
                return Domain(domain.value)
            if domain.operator == "not any":
                return ~Domain(domain.value)
            return Domain("id", domain.operator, domain.value)
        if field_expr.startswith("location_id."):
            return Domain(
                field_expr.removeprefix("location_id."),
                domain.operator,
                domain.value,
            )
    return None


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_location_for_locations(self):
        """
        Adapt the domain computed for stock.quant for stock.location
        """
        quant_domain = self._get_domain_locations()[0]
        location_domain = _extract_location_domain(Domain(quant_domain))
        return Domain.TRUE if location_domain is None else location_domain
