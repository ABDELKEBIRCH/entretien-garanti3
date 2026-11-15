"""Optional SMTP notifications for interview confirmations."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_STARTTLS, SMTP_USER


def envoyer_confirmation_entretien(destinataire: str, nom: str, poste: str, entreprise: str,
                                   date: str = "", lieu: str = "", notes: str = "") -> bool:
    if not SMTP_HOST or not SMTP_FROM:
        return False
    message = EmailMessage()
    message["Subject"] = f"Entretien confirmé — {poste}"
    message["From"] = SMTP_FROM
    message["To"] = destinataire
    details = [f"Bonjour {nom},", "", f"Votre entretien pour le poste « {poste} » chez {entreprise or 'l’entreprise'} est confirmé."]
    if date:
        details.append(f"Date et heure : {date}")
    if lieu:
        details.append(f"Lieu ou lien : {lieu}")
    if notes:
        details.extend(["", f"Informations complémentaires : {notes}"])
    details.extend(["", "Bonne préparation,", "L’équipe Entretien garanti"])
    message.set_content("\n".join(details))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        if SMTP_STARTTLS:
            server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)
    return True
