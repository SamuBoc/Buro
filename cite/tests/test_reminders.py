"""
Tests - HU-17: Enviar recordatorios automáticos de citas
Requerimiento Funcional: RF15
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from beneficiary.models import Beneficiary
from cite.models import Cite
from cite.scheduler import send_cite_reminders


def make_beneficiary(name='Ana Lopez', email='ana@test.com'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3001234567',
        email=email,
    )


def make_cite(beneficiary, days_ahead=1, state=Cite.STATE_PENDING, reminder_sent=False):
    return Cite.objects.create(
        beneficiary=beneficiary,
        date_assigned=date.today() + timedelta(days=days_ahead),
        modality_cite=Cite.MODALITY_INPERSON,
        state_cite=state,
        request_cite=Cite.CHANNEL_WEB,
        description='Consulta jurídica.',
        reminder_sent=reminder_sent,
    )


class HU17_RecordatorioEnviadoTest(TestCase):

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_recordatorio_enviado_para_cita_de_manana(self, mock_email):
        """POSITIVO: Se envía recordatorio al beneficiario con cita programada para mañana."""
        b = make_beneficiary()
        cite = make_cite(b, days_ahead=1)
        mock_email.return_value.send.return_value = True

        send_cite_reminders()

        mock_email.assert_called_once()
        cite.refresh_from_db()
        self.assertTrue(cite.reminder_sent)

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_reminder_sent_se_marca_true_tras_envio(self, mock_email):
        """POSITIVO: El campo reminder_sent queda en True después de enviar el recordatorio."""
        b = make_beneficiary(email='b@test.com')
        cite = make_cite(b, days_ahead=1)
        mock_email.return_value.send.return_value = True

        send_cite_reminders()

        cite.refresh_from_db()
        self.assertTrue(cite.reminder_sent)

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_recordatorio_para_cita_confirmada(self, mock_email):
        """POSITIVO: También se envía recordatorio para citas en estado Confirmada."""
        b = make_beneficiary(email='c@test.com')
        cite = make_cite(b, days_ahead=1, state=Cite.STATE_CONFIRMED)
        mock_email.return_value.send.return_value = True

        send_cite_reminders()

        mock_email.assert_called_once()


class HU17_RecordatorioNoEnviadoTest(TestCase):

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_no_recordatorio_para_cita_cancelada(self, mock_email):
        """NEGATIVO: No se envía recordatorio para citas canceladas."""
        b = make_beneficiary(email='d@test.com')
        make_cite(b, days_ahead=1, state=Cite.STATE_CANCELED)

        send_cite_reminders()

        mock_email.assert_not_called()

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_no_recordatorio_para_cita_no_de_manana(self, mock_email):
        """NEGATIVO: No se envía recordatorio para citas que no son mañana."""
        b = make_beneficiary(email='e@test.com')
        make_cite(b, days_ahead=3)

        send_cite_reminders()

        mock_email.assert_not_called()

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_no_duplicado_si_ya_se_envio(self, mock_email):
        """NEGATIVO: No se envía un segundo recordatorio si ya fue enviado."""
        b = make_beneficiary(email='f@test.com')
        make_cite(b, days_ahead=1, reminder_sent=True)

        send_cite_reminders()

        mock_email.assert_not_called()

    @patch('cite.scheduler.logger')
    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_no_recordatorio_sin_email_registra_warning(self, mock_email, mock_logger):
        """NEGATIVO: Sin email del beneficiario no se envía y se registra warning en log."""
        b = make_beneficiary(name='Sin Email', email='')
        b.email = ''
        b.save()
        make_cite(b, days_ahead=1)

        send_cite_reminders()

        mock_email.assert_not_called()
        mock_logger.warning.assert_called()


class HU17_VolumenTest(TestCase):

    @patch('cite.scheduler.EmailMultiAlternatives')
    def test_recordatorios_para_multiples_citas(self, mock_email):
        """VOLUMEN: Se envían recordatorios correctamente para 20 citas de mañana."""
        mock_email.return_value.send.return_value = True

        for i in range(20):
            b = Beneficiary.objects.create(
                name=f'Beneficiario {i}',
                location='Cali',
                phone=f'300{i:07d}',
                email=f'ben{i}@test.com',
            )
            make_cite(b, days_ahead=1)

        send_cite_reminders()

        self.assertEqual(mock_email.call_count, 20)
        self.assertEqual(
            Cite.objects.filter(reminder_sent=True).count(), 20
        )