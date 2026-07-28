"""Mail System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.mail import Mail, MailAttachment
from datetime import datetime

mail_bp = Blueprint('mail', __name__, url_prefix='/mail')


@mail_bp.route('/')
def inbox():
    """Mail inbox page"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    page = request.args.get('page', 1, type=int)
    mail_type = request.args.get('type', 'all')

    query = Mail.query.filter_by(user_id=current_user.id)
    if mail_type != 'all':
        query = query.filter_by(mail_type=mail_type)

    mails = query.order_by(Mail.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    unread_count = Mail.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('mail/inbox.html', mails=mails, unread_count=unread_count,
                           mail_type=mail_type)


@mail_bp.route('/<int:mail_id>')
@login_required
def view_mail(mail_id):
    """View a specific mail"""
    mail = Mail.query.get_or_404(mail_id)

    if mail.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if not mail.is_read:
        mail.is_read = True
        db.session.commit()

    attachments = mail.attachments.all()

    return render_template('mail/view.html', mail=mail, attachments=attachments)


@mail_bp.route('/<int:mail_id>/claim', methods=['POST'])
@login_required
def claim_mail(mail_id):
    """Claim mail attachments"""
    mail = Mail.query.get_or_404(mail_id)

    if mail.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    if mail.is_claimed:
        return jsonify({'error': 'Already claimed'}), 400

    attachments = mail.attachments.all()
    total_coins = 0
    total_xp = 0
    items_claimed = []

    for attachment in attachments:
        if attachment.is_claimed:
            continue

        if attachment.item_type == 'coins':
            total_coins += attachment.quantity * attachment.item_id  # item_id stores coin amount
            attachment.is_claimed = True
        elif attachment.item_type == 'xp':
            total_xp += attachment.quantity
            attachment.is_claimed = True
        else:
            items_claimed.append({
                'type': attachment.item_type,
                'item_id': attachment.item_id,
                'quantity': attachment.quantity
            })
            attachment.is_claimed = True

    current_user.coins += total_coins
    if total_xp > 0:
        current_user.add_xp(total_xp)

    mail.is_claimed = True
    db.session.commit()

    return jsonify({
        'success': True,
        'coins': total_coins,
        'xp': total_xp,
        'items': items_claimed
    })


@mail_bp.route('/claim-all', methods=['POST'])
@login_required
def claim_all():
    """Claim all mail attachments"""
    unread_mails = Mail.query.filter_by(
        user_id=current_user.id,
        is_claimed=False,
        has_attachments=True
    ).all()

    total_coins = 0
    total_xp = 0
    claimed_count = 0

    for mail in unread_mails:
        for attachment in mail.attachments.all():
            if attachment.is_claimed:
                continue
            if attachment.item_type == 'coins':
                total_coins += attachment.quantity * attachment.item_id
            elif attachment.item_type == 'xp':
                total_xp += attachment.quantity
            attachment.is_claimed = True
            mail.is_claimed = True
            claimed_count += 1

    current_user.coins += total_coins
    if total_xp > 0:
        current_user.add_xp(total_xp)

    db.session.commit()

    flash(f'Claimed rewards from {claimed_count} attachments!', 'success')
    return jsonify({'success': True, 'coins': total_coins, 'xp': total_xp, 'count': claimed_count})


@mail_bp.route('/<int:mail_id>/delete', methods=['POST'])
@login_required
def delete_mail(mail_id):
    """Delete a mail"""
    mail = Mail.query.get_or_404(mail_id)

    if mail.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    db.session.delete(mail)
    db.session.commit()

    return jsonify({'success': True})


@mail_bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread mail count"""
    count = Mail.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


# API endpoints
@mail_bp.route('/api/inbox')
@login_required
def api_inbox():
    """API: Get inbox"""
    page = request.args.get('page', 1, type=int)
    mails = Mail.query.filter_by(user_id=current_user.id).order_by(
        Mail.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)

    return jsonify({
        'mails': [m.to_dict() for m in mails.items],
        'total': mails.total,
        'pages': mails.pages
    })


@mail_bp.route('/api/send', methods=['POST'])
@login_required
def api_send():
    """API: Send a mail (admin/system)"""
    from app.utils.admin import admin_required

    # Only admin can send system mails
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    target_user_id = request.json.get('user_id')
    if not target_user_id:
        return jsonify({'error': 'User ID required'}), 400

    mail = Mail(
        user_id=target_user_id,
        sender_id=current_user.id,
        sender_type='admin',
        subject=request.json.get('subject', ''),
        body=request.json.get('body', ''),
        mail_type='system'
    )
    db.session.add(mail)
    db.session.commit()

    return jsonify({'success': True, 'mail_id': mail.id})
