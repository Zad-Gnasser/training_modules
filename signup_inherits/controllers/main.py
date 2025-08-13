from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request

class SignUpInherits(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        res = super(SignUpInherits, self).web_auth_signup(*args, **kw)
        mobile_value = kw.get('mobile')
        if mobile_value:
            user = request.env['res.users'].sudo().search([("login", "=", kw.get("login"))], limit=1)
            if user:
                user.partner_id.sudo().mobile = mobile_value
        return res
