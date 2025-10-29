# 🔐 USB Signature & Biometric Authentication Setup Guide

## ✅ Completed Setup

Your HR system now includes comprehensive USB signature pad and biometric (fingerprint) authentication support!

## 🎯 Features Implemented

### 1. **Signature Methods** (4 options)
- ✏️ **Draw Signature** - Canvas-based signature drawing
- ⌨️ **Type Name** - Typed signature with custom font
- 🖊️ **USB Signature Pad** - Hardware signature device via Web USB API
- 👆 **Biometric (Fingerprint)** - Fingerprint authentication via WebAuthn API

### 2. **Device Management**
- **Device Registration** - Register USB pads, fingerprint readers, face cameras, iris scanners
- **Auto-Detection** - JavaScript-based automatic device detection
- **Admin Verification** - Devices require admin approval before use
- **Security Features**:
  - Device locking after 5 failed attempts (30-minute lockout)
  - Device serial number tracking
  - Last used timestamp tracking
  - Device activation/deactivation

### 3. **Navigation**
New sidebar section "Signatures" with:
- 📋 **Mes demandes** - View signature requests (with pending count badge)
- 🔐 **Mes dispositifs** - Manage your USB/biometric devices
- 📊 **Tableau de bord** - Admin dashboard (IT Admin/HR Admin only)

### 4. **Permissions**
Role-based access configured:
- **IT Admin**: Full access (view, sign, request, reject, verify, admin)
- **HR Admin**: View, sign, request, verify
- **Manager**: View, sign
- **HR View**: View, sign

## 🚀 How to Use

### For Users: Register a Device

1. **Navigate to Signatures**:
   - Sidebar → Signatures → Mes dispositifs

2. **Register USB Signature Pad**:
   - Click "Enregistrer un nouveau dispositif"
   - Select device type: "Tablette de signature USB"
   - Click "Détecter automatiquement"
   - Browser will prompt for USB device permission
   - Connect your USB signature pad
   - Grant permission when prompted
   - Device details will auto-fill
   - Click "Enregistrer"

3. **Register Fingerprint Reader**:
   - Click "Enregistrer un nouveau dispositif"
   - Select device type: "Lecteur d'empreintes digitales"
   - Click "Détecter automatiquement"
   - Follow fingerprint enrollment prompts
   - Your fingerprint will be registered with WebAuthn
   - Click "Enregistrer"

4. **Wait for Admin Approval**:
   - Device status will show "Pending Verification"
   - Admin must verify device in Django admin
   - Once verified, you can use it for signatures

### For Users: Sign Documents

1. **Navigate to Signature Request**:
   - You'll receive notification when signature requested
   - Click notification or go to Signatures → Mes demandes

2. **Choose Signature Method**:
   - **Draw**: Use mouse/touch to draw signature
   - **Type**: Type your name (appears in signature font)
   - **USB Device**: Select registered USB pad and draw
   - **Biometric**: Use fingerprint reader

3. **Submit Signature**:
   - Click "Soumettre la signature"
   - Signature is verified with SHA256 hash
   - Timestamp and IP recorded for audit trail

### For Admins: Verify Devices

1. **Django Admin Panel**:
   - Go to http://localhost:8000/admin/
   - Navigate to Signatures → Biometric Devices

2. **Verify Devices**:
   - Select unverified devices
   - Actions → "Verify selected devices"
   - Devices now available for use

3. **View Signature Dashboard**:
   - Sidebar → Signatures → Tableau de bord
   - View signature statistics and analytics

## 🌐 Browser Compatibility

### Web USB API (USB Signature Pads)
- ✅ **Chrome/Chromium** - Full support
- ✅ **Microsoft Edge** - Full support
- ❌ **Firefox** - Not supported
- ❌ **Safari** - Not supported

### WebAuthn API (Biometric)
- ✅ **Chrome** - Full support
- ✅ **Edge** - Full support
- ✅ **Firefox** - Full support
- ✅ **Safari** - Full support (iOS 14+)

**Recommendation**: Use Chrome or Edge for best compatibility with both features.

## 🔧 Supported Devices

### USB Signature Pads
- Wacom STU series
- Topaz SignatureGem
- Scriptel ScripTouch
- Any HID-compliant USB signature tablet

### Biometric Devices
- **Fingerprint**: Windows Hello, Touch ID, USB fingerprint readers
- **Face Recognition**: Windows Hello face camera, Face ID
- **Iris Scanners**: Windows Hello iris scanner

## 🔒 Security Features

1. **Device Verification**: Admin must approve new devices
2. **Failed Attempt Limiting**: 5 failed attempts = 30-minute lockout
3. **Audit Trail**: All signatures tracked with:
   - Timestamp
   - IP address
   - Device used
   - Signature method
   - SHA256 verification hash
4. **Device Fingerprinting**: Unique device identification
5. **Session Security**: Biometric credentials stored securely in browser

## 📋 Integration with Workflows

The signature system automatically integrates with:
- **Leave Requests** - Manager approval signatures
- **Deployments (Ordre de Mission)** - Multiple approval signatures
- **Document Generation** - Official document signing

When a signature is required, users receive a notification and can sign using any registered method.

## 🛠️ Troubleshooting

### USB Device Not Detected
1. Ensure device is connected
2. Use Chrome or Edge browser
3. Grant USB permission when prompted
4. Check device is HID-compliant
5. Try different USB port

### Fingerprint Not Working
1. Verify biometric device is set up in Windows/macOS
2. Test Windows Hello/Touch ID first
3. Clear browser data and re-register
4. Ensure device is not locked (check last attempt time)

### Device Shows "Pending"
- Wait for admin to verify in Django admin
- Contact IT admin if takes > 24 hours

### Signature Rejected
- Check device is verified and active
- Ensure device is not locked
- Try alternative signature method

## 📞 Support

For technical issues:
- **IT Admin**: Check Django admin → Biometric Devices
- **Users**: Use "Draw" or "Type" as fallback methods
- **Logs**: Check Docker logs for detailed errors

## 🎉 Success!

Your signature system is now fully operational with:
- ✅ USB signature pad support
- ✅ Fingerprint authentication
- ✅ Device management
- ✅ Role-based permissions
- ✅ Sidebar navigation
- ✅ Audit trail

**Next Steps**: Register your USB device and start signing documents electronically!
