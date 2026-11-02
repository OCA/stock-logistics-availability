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


def _extract_subdomain(domain, submodel_field):
    """Return the conditions of ``domain`` on ``submodel_field``, for its model.

    Return ``None`` when no condition is left.
    """
    if isinstance(domain, DomainBool):
        return domain
    if isinstance(domain, DomainNary):
        children = [
            child
            for child in (
                _extract_subdomain(child, submodel_field) for child in domain.children
            )
            if child is not None
        ]
        if not children:
            return None
        if isinstance(domain, DomainAnd):
            return Domain.AND(children)
        return Domain.OR(children)
    if isinstance(domain, DomainNot):
        child = _extract_subdomain(domain.child, submodel_field)
        return None if child is None else ~child
    if isinstance(domain, DomainCondition):
        field_expr = domain.field_expr
        if field_expr == submodel_field:
            if domain.operator == "any":
                return Domain(domain.value)
            if domain.operator == "not any":
                return ~Domain(domain.value)
            return Domain("id", domain.operator, domain.value)
        if field_expr.startswith(f"{submodel_field}."):
            return Domain(
                field_expr.removeprefix(f"{submodel_field}."),
                domain.operator,
                domain.value,
            )
    return None


def extract_subdomains(domain, submodel_field):
    """Extract the subdomains on a submodel from a domain-like structure.

    The conditions on other fields are removed, along with the operators left
    without operands.

    :param domain: a domain-like structure
    :param submodel_field: the field name of the submodel
    :return: a ``Domain`` on the submodel
    """
    subdomain = _extract_subdomain(Domain(domain), submodel_field)
    return Domain.TRUE if subdomain is None else subdomain


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_location_for_locations(self):
        """
        Adapt the domain computed for stock.quant for stock.location
        """
        quant_domain = self._get_domain_locations()[0]
        return extract_subdomains(quant_domain, "location_id")
