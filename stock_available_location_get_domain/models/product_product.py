# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import itertools

from odoo import models
from odoo.osv import expression
from odoo.osv.expression import (
    DOMAIN_OPERATORS,
    FALSE_LEAF,
    TERM_OPERATORS,
    TERM_OPERATORS_NEGATION,
    TRUE_LEAF,
)

# The following methods comes from odoo 18.0 odoo.osv.expression
# Copyrigth Odoo SA


def _tree_from_domain(domain):
    """Return the domain as a tree, with the following structure::

        <tree> ::= ('?', <boolean>)
                |  ('!', <tree>)
                |  ('&', <tree>, <tree>, ...)
                |  ('|', <tree>, <tree>, ...)
                |  (<comparator>, <fname>, <value>)

    By construction, AND (``&``) and OR (``|``) nodes are n-ary and have at
    least two children.  Moreover, AND nodes (respectively OR nodes) do not have
    AND nodes (resp. OR nodes) in their children.
    """
    stack = []
    for item in reversed(domain):
        if item == "!":
            stack.append(_tree_not(stack.pop()))
        elif item == "&":
            stack.append(_tree_and((stack.pop(), stack.pop())))
        elif item == "|":
            stack.append(_tree_or((stack.pop(), stack.pop())))
        elif item == TRUE_LEAF:
            stack.append(("?", True))
        elif item == FALSE_LEAF:
            stack.append(("?", False))
        else:
            lhs, comparator, rhs = item
            if comparator in ("any", "not any"):
                rhs = _tree_from_domain(rhs)
            stack.append((comparator, lhs, rhs))
    return _tree_and(reversed(stack))


def _tree_not(tree):
    """Negate a tree node."""
    if tree[0] == "=?":
        # already update operator '=?' here, so that '!' is distributed correctly
        assert len(tree) == 3
        if tree[2]:
            tree = ("=", tree[1], tree[2])
        else:
            return ("?", False)
    if tree[0] == "?":
        return ("?", not tree[1])
    if tree[0] == "!":
        return tree[1]
    if tree[0] == "&":
        return ("|", *(_tree_not(item) for item in tree[1:]))
    if tree[0] == "|":
        return ("&", *(_tree_not(item) for item in tree[1:]))
    if tree[0] in TERM_OPERATORS_NEGATION:
        return (TERM_OPERATORS_NEGATION[tree[0]], tree[1], tree[2])
    return ("!", tree)


def _tree_and(trees):
    """Return the tree given by AND-ing all the given trees."""
    children = []
    for tree in trees:
        if tree == ("?", True):
            pass
        elif tree == ("?", False):
            return tree
        elif tree[0] == "&":
            children.extend(tree[1:])
        else:
            children.append(tree)
    if not children:
        return ("?", True)
    if len(children) == 1:
        return children[0]
    return ("&", *children)


def _tree_or(trees):
    """Return the tree given by OR-ing all the given trees."""
    children = []
    for tree in trees:
        if tree == ("?", True):
            return tree
        elif tree == ("?", False):
            pass
        elif tree[0] == "|":
            children.extend(tree[1:])
        else:
            children.append(tree)
    if not children:
        return ("?", False)
    if len(children) == 1:
        return children[0]
    return ("|", *children)


# End of copyrigth Odoo SA


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
        if submodel_field in fname:
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
    tree = _tree_from_domain(domain)
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
