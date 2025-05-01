# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime


class TransitLog(models.Model):
    _name = "transit.log"
    _description = "Bitácora de Tránsitos Punto A–B"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _mail_post_on_create = True          # registra mensaje al crear

    # ─── Cabecera ────────────────────────────────────────────────────────────
    name = fields.Char(
        string="Folio",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nuevo"),
        tracking=True,
    )
    # ← Se quita el default; se llena manualmente o con el botón “Salir”
    date_start = fields.Datetime(string="Salida", tracking=True)
    date_end   = fields.Datetime(string="Llegada", tracking=True)

    origin      = fields.Char(string="Origen",      required=True, tracking=True)
    destination = fields.Char(string="Destino",    required=True, tracking=True)

    state = fields.Selection(
        [
            ("draft",     "Borrador"),
            ("in_transit","En tránsito"),
            ("delivered", "Entregado"),
            ("cancelled", "Cancelado"),
        ],
        string="Estado",
        default="draft",
        tracking=True,
    )

    line_ids = fields.One2many(
        "transit.log.line",
        "log_id",
        string="Productos transportados",
    )
    notes = fields.Text(string="Notas adicionales", tracking=True)

    # ─── Secuencia ──────────────────────────────────────────────────────────
    @api.model
    def create(self, vals):
        if vals.get("name", _("Nuevo")) == _("Nuevo"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "transit.log.sequence"
            ) or _("Nuevo")
        return super().create(vals)

    # ─── Acciones de flujo ──────────────────────────────────────────────────
    def action_start(self):
        """Cambia a EN TRÁNSITO y, si 'date_start' está vacío, lo llena con 'ahora'."""
        for rec in self:
            if not rec.date_start:
                rec.date_start = fields.Datetime.now()
            rec.state = "in_transit"

    def action_arrive(self):
        for rec in self:
            rec.state    = "delivered"
            rec.date_end = fields.Datetime.now()

    def action_cancel(self):
        self.state = "cancelled"


class TransitLogLine(models.Model):
    _name = "transit.log.line"
    _description = "Detalle de productos en tránsito"
    _inherit = ["mail.thread"]
    _tracking_parent_field = "log_id"     # → el diff va al chatter del padre

    log_id = fields.Many2one(
        "transit.log",
        string="Bitácora",
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        required=True,
        tracking=True,
    )
    product_uom_qty = fields.Float(
        string="Cantidad",
        required=True,
        digits="Product Unit of Measure",
        tracking=True,
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="UdM",
        required=True,
        domain="[('category_id', '=', product_id.uom_id.category_id)]",
        tracking=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
