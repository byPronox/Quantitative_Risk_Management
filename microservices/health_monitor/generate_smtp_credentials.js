const nodemailer = require('nodemailer');

// Crear cuenta de prueba Ethereal (auto-genera credenciales)
async function createTestAccount() {
    const testAccount = await nodemailer.createTestAccount();

    console.log('═══════════════════════════════════════════════════');
    console.log('📧 CREDENCIALES SMTP GENERADAS (Ethereal Email)');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('Copia estas credenciales en tu archivo .env:');
    console.log('');
    console.log(`SMTP_HOST=smtp.ethereal.email`);
    console.log(`SMTP_PORT=587`);
    console.log(`SMTP_USER=${testAccount.user}`);
    console.log(`SMTP_PASS=${testAccount.pass}`);
    console.log('');
    console.log('═══════════════════════════════════════════════════');
    console.log('');
    console.log('Los emails se podrán ver en: https://ethereal.email/messages');
    console.log('Usuario:', testAccount.user);
    console.log('Contraseña:', testAccount.pass);
    console.log('');
}

createTestAccount().catch(console.error);
