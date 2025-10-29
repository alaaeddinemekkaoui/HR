# 🔐 USB Digital Stamp - Quick Setup Guide

## Overview
Your HR system now supports **USB Digital Stamp** - a password-protected digital seal/stamp image stored on USB that can be used for official document signing.

## ✅ What's Fixed
1. **Register Button** - Now works immediately (no longer disabled)
2. **Admin Approval** - BiometricDevice admin properly configured with verification actions
3. **Stamp Preview** - Admin can see stamp preview in Django admin

---

## 📋 For Users: How to Register USB Digital Stamp

### Step 1: Navigate to Device Registration
1. Click **Signatures** in sidebar
2. Click **Mes dispositifs** (My devices)
3. Click **Enregistrer un nouveau dispositif** (Register new device)

### Step 2: Select Device Type
1. Choose: **USB Digital Stamp (Password Protected)**
2. Device details auto-fill:
   - Device Name: "USB Digital Stamp"
   - Device Serial: Auto-generated

### Step 3: Upload Stamp Image
1. Click **Select Stamp Image from USB**
2. Browse your USB drive
3. Select your official company stamp/seal image (PNG, JPG, SVG)
4. Preview appears automatically

### Step 4: Set Password Protection
1. Enter secure password (minimum 6 characters)
2. Confirm password
3. **Important**: Remember this password! You'll need it every time you sign

### Step 5: Submit Registration
1. Click **Register Device**
2. You'll see: "USB Digital Stamp Device (Password Protected) registered! Awaiting admin verification."

### Step 6: Wait for Admin Approval
- Status shows "Pending Verification"
- Admin must verify in Django admin
- You'll receive notification when approved

---

## 👨‍💼 For Admins: How to Approve USB Stamps

### Access Admin Panel
1. Go to: **http://localhost:8000/admin/**
2. Login with admin credentials
3. Navigate to: **Signatures → Biometric Devices**

### View Pending Devices
- Filter by: **Is verified: No**
- You'll see all unverified devices including USB stamps
- Device type shows: "USB Digital Stamp Device (Password Protected)"

### Review Device Details
Click on device to see:
- **User**: Who registered it
- **Device Type**: usb_stamp_device
- **Device Name**: USB Digital Stamp
- **Stamp Preview**: Click "USB Stamp Data" section to see image

### Verify Device
**Option 1: Single Device**
1. Open device
2. Check **Is verified** checkbox
3. Click **Save**

**Option 2: Bulk Verification**
1. Select multiple devices (checkboxes)
2. Actions dropdown → **Verify selected devices**
3. Click **Go**
4. Confirmation: "X device(s) verified successfully"

### Deactivate Device (if needed)
1. Select device(s)
2. Actions → **Deactivate selected devices**
3. Or uncheck **Is active** in device details

---

## 🖊️ For Users: How to Sign with USB Stamp

### Step 1: Signature Request
1. You'll receive notification for signature request
2. Click notification or go to **Signatures → Mes demandes**
3. Click on document to sign

### Step 2: Choose USB Digital Stamp
1. Select signature method: **📌 USB Digital Stamp**
2. USB stamp section appears

### Step 3: Select Your Device
1. Dropdown shows: "IAV Hassan II Official Stamp (USB)"
2. Select your registered device
3. Password field appears

### Step 4: Unlock Stamp
1. Enter your stamp password
2. Click **🔓 Unlock** button
3. System verifies password

### Step 5: Review and Sign
1. Stamp preview appears (if password correct)
2. Shows: "Official Company Seal"
3. Badge: ✅ Stamp Unlocked
4. Click **Sign Document**

### Security Features
- **5 Failed Attempts** → Device locked for 30 minutes
- **Attempts Remaining** shown on wrong password
- **IP and Timestamp** recorded for audit trail

---

## 🔒 Security Features

### Password Protection
- SHA256 hashed passwords (never stored in plain text)
- Minimum 6 characters required
- Failed attempt tracking

### Device Locking
- 5 failed password attempts = 30-minute lockout
- Automatic unlock after timeout
- Failed attempts counter resets on success

### Admin Verification
- All devices require admin approval
- Prevents unauthorized stamp registration
- Admin can deactivate compromised devices

### Audit Trail
Every signature includes:
- Timestamp
- IP address
- Device serial number
- User agent
- Password verification status

---

## 🎯 Use Cases

### Official Documents
- **Leave Requests** - HR Admin approval with official stamp
- **Deployments** - Director signature with company seal
- **Certificates** - Official IAV Hassan II stamp

### Workflow Example: Deployment Approval
1. Employee creates deployment request
2. Manager signs (fingerprint/drawn)
3. HR Admin signs (USB digital stamp with password)
4. Director signs (USB digital stamp with password)
5. All signatures recorded with audit trail

---

## ⚠️ Troubleshooting

### "Nothing happens when I click Register"
- ✅ **FIXED** - Button now enabled by default
- Make sure all fields are filled
- Check browser console for errors (F12)

### "Can't see approval in admin"
- ✅ **FIXED** - BiometricDevice properly registered
- Login as superuser or IT Admin
- Go to /admin/signatures/biometricdevice/
- Filter by "Is verified: No"

### "Invalid Password" Error
- Double-check password (case-sensitive)
- Check attempts remaining
- If locked, wait 30 minutes
- Contact admin to reset device

### "Device Not Found"
- Ensure device is verified by admin
- Check device is active
- Try registering again if needed

### "Stamp Image Not Loading"
- Verify image was uploaded during registration
- Check file format (PNG, JPG, SVG)
- Admin: Check "stamp_image_path" field
- Re-register device if needed

---

## 📊 Admin Dashboard Features

### Device List Columns
- **ID** - Device identifier
- **User** - Who owns the device
- **Device Type** - usb_stamp_device
- **Device Name** - "USB Digital Stamp"
- **Is Verified** ✅ or ❌
- **Is Active** ✅ or ❌
- **Failed Attempts** - Security counter
- **Registered At** - Registration date
- **Last Used At** - Most recent use

### Bulk Actions
- **Verify selected devices** - Approve multiple at once
- **Deactivate selected devices** - Disable compromised devices

### Fieldsets
1. **Device Information** - Basic details
2. **Status** - Verification, active status, lock info
3. **Biometric Data** - Enrollment data (collapsed)
4. **USB Stamp Data** - Password hash, stamp image (collapsed)
5. **Timestamps** - Registration and usage dates

---

## 🎉 Benefits

### For Users
- ✅ Official company seal on documents
- ✅ Password protected (secure)
- ✅ Easy to use (upload once, use forever)
- ✅ Works on any computer (device registered to user)

### For Admins
- ✅ Full control over stamp approvals
- ✅ See stamp preview before approval
- ✅ Track all stamp usage
- ✅ Revoke access instantly (deactivate device)
- ✅ Security monitoring (failed attempts)

### For Organization
- ✅ Official document signing
- ✅ Legal compliance (electronic signature law)
- ✅ Complete audit trail
- ✅ Reduced paper usage
- ✅ Faster approval workflows

---

## 🚀 Next Steps

1. **Register your USB stamp** (if you have authorization)
2. **Wait for admin verification** (check notifications)
3. **Test on sample document** (practice signing)
4. **Use for official documents** (deployments, leaves)

## 📞 Support

- **Registration Issues**: Contact IT Admin
- **Password Reset**: Contact IT Admin (device must be re-registered)
- **Verification Pending**: Contact HR Admin
- **Technical Issues**: Check Django admin logs

---

## ✨ System Status

- ✅ Database migration applied
- ✅ Models updated with stamp fields
- ✅ Views support stamp signing
- ✅ Templates updated
- ✅ Admin interface configured
- ✅ Security features enabled
- ✅ Audit trail active

**Your USB Digital Stamp system is fully operational!** 🎉
