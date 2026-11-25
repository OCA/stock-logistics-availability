For a third party to be able to check their consigned stock from the
Portal:

1.  Create or identify the `res.partner` that will act as the owner of
    the goods.
2.  Register the corresponding stock in `stock.quant` by setting the
    `owner_id` field to that partner (via the standard
    reception-with-ownership processes, or via the "Update Quantity"
    wizard specifying the owner).
3.  Grant Portal access to a user linked to that partner (or to a child
    contact of the same commercial entity).

No additional configuration is required: the module does not introduce
any system parameters or specific settings.
