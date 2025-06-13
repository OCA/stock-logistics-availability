# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import itertools

from odoo import models
from odoo.osv import expression
from odoo.osv.expression import (
    DOMAIN_OPERATORS,
    TERM_OPERATORS,
)


def _extract_subtree(tree, submodel_field):
    result_tree = []
    op = tree[0]
    if op in DOMAIN_OPERATORS:
        for subdomain in tree[1:]:
            subtree = _extract_subtree(subdomain, submodel_field)
            if subtree:
                result_tree.append(subtree)
        if len(result_tree) == 1:
            result_tree = result_tree[0]
        else:
            result_tree = (op, *result_tree)
    elif op in TERM_OPERATORS:
        fname = tree[1]
        # Handles 'any' operator domains on related fields, e.g.:
        # ('location_id', 'any', [('parent_path', '=like', '1/7/8/%')]).
        # Extracts subfields(e.g., 'parent_path') to evaluate the domain
        # on the related model.
        if op == "any":
            result_tree = tree[2]
        elif submodel_field in fname:
            if fname == submodel_field:
                fname = "id"
            else:
                fname = fname.replace(submodel_field + ".", "")
            result_tree = (op, fname, tree[2])
    return result_tree


def _tree_to_domain(tree):
    """Convert a tree to a domain."""
    op = tree[0]
    result = []
    if op in DOMAIN_OPERATORS:
        sub_flattened = [_tree_to_domain(item) for item in tree[1:]]
        # the subtree is a n-ary operator. We need to add n-1 operator
        # to become a valid domain
        result.extend(op * (len(sub_flattened) - 1))
        result.extend(itertools.chain.from_iterable(sub_flattened))
    elif op in TERM_OPERATORS:
        result = (tree[1], op, tree[2])
    return result


def tree_to_domain(tree):
    """Convert a tree to a domain."""
    flattened = _tree_to_domain(tree)
    result_domain = []
    leaf = []
    for item in flattened:
        if item in DOMAIN_OPERATORS:
            leaf = []
            result_domain.append(item)
        else:
            leaf.append(item)
            if len(leaf) == 3:
                result_domain.append(tuple(leaf))
                leaf = []
    return result_domain


def extract_subdomains(domain, submodel_field):
    """Extract the subdomains from a domain-like structure.

    :param domain: a domain-like structure
    :param submodel_field: the field name of the submodel
    :return: a list of subdomains
    """
    domain = expression.normalize_domain(domain)
    domain = expression.distribute_not(domain)
    tree = expression._tree_from_domain(domain)
    subtree = _extract_subtree(tree, submodel_field)
    domain = []
    if subtree:
        domain = tree_to_domain(subtree)
    if expression.is_leaf(domain):
        domain = [domain]
    return domain


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_domain_location_for_locations(self):
        """
        Adapt the domain computed for stock.quant for stock.location
        """
        quant_domain = self._get_domain_locations()[0]
        subdomain = extract_subdomains(quant_domain, "location_id")
        return subdomain
