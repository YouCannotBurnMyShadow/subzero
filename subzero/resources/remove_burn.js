
// we may have a problem with escaped quotes
var oReg = new ActiveXObject('winmgmts:{impersonationLevel=impersonate}!\\.\root\default:StdRegProv');
var HKEY_LOCAL_MACHINE = 2147483650;
var strKeyPath = 'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall';

oReg.EnumKey(HKEY_LOCAL_MACHINE, strKeyPath, arrSubKeys);
for(var strSubkey in arrSubKeys) {
    var strSubKeyPath = strKeyPath + '\\' + strSubkey;
    oReg.EnumValues(HKEY_LOCAL_MACHINE, strSubKeyPath, arrValueNames, arrTypes);
    var upgradeCode = null;
    var uninstallString = null;
    var quietUninstallString = null;
    i = 0;
    for(strValueName in arrValueNames) {
        switch(arrTypes[i]) {
          case REG_SZ:
            oReg.GetStringValue(HKEY_LOCAL_MACHINE, strSubKeyPath, strValueName, strValue);
            switch(strValueName) {
                case 'BundleUpgradeCode':
                    upgradeCode = strValue;
                case 'UninstallString':
                    uninstallString = strValue;
                case 'QuietUninstallString':
                    quietUninstallString = strValue;
            }
        }
        i++;
    }

    if(upgradeCode == '{UpgradeCode}') {
        var command = null;
        if(quietUninstallString)
            command = quietUninstallString;
        else if(uninstallString)
            command = uninstallString;

        if(command) {
            // Run it!
            var oShell = WScript.CreateObject("WScript.Shell");
            oShell.Exec(command);
        }
    }
}