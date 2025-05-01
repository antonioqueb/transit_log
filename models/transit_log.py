# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime

class TransitLog(models.Model):
    _name = "transit.log"
    _description = "Bitácora de Tránsitos Punto A–B"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Cabecera
    name = fields.Char(
        string="Folio",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nuevo"),
    )
    date_start = fields.Datetime(
        string="Salida",
        tracking=True,
        default=lambda self: fields.Datetime.now(),
    )
    date_end = fields.Datetime(string="Llegada", tracking=True)
    origin = fields.Char(string="Origen", tracking=True, required=True)
    destination = fields.Char(string="Destino", tracking=True, required=True)

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_transit", "En tránsito"),
            ("delivered", "Entregado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )

    line_ids = fields.One2many(
        "transit.log.line", "log_id", string="Productos transportados"
    )
    notes = fields.Text(string="Notas adicionales")

    # Secuencia automática
    @api.model
    def create(self, vals):
        if vals.get("name", _("Nuevo")) == _("Nuevo"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "transit.log.sequence"
            ) or _("Nuevo")
        return super().create(vals)

    # Acciones simples de flujo
    def action_start(self):
        self.state = "in_transit"

    def action_arrive(self):
        self.state = "delivered"
        self.date_end = fields.Datetime.now()

    def action_cancel(self):
        self.state = "cancelled"


class TransitLogLine(models.Model):
    _name = "transit.log.line"
    _description = "Detalle de productos en tránsito"

    log_id = fields.Many2one("transit.log", string="Bitácora", ondelete="cascade")
    product_id = fields.Many2one(
        "product.product", string="Producto", required=True
    )
    product_uom_qty = fields.Float(
        string="Cantidad", required=True, digits="Product Unit of Measure"
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="UdM",
        required=True,
        domain="[('category_id', '=', product_id.uom_id.category_id)]",
    )

    # Al seleccionar producto, proponemos la UdM por defecto
    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
