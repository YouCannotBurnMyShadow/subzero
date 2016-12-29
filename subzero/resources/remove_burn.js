
//
// CustomActions.js
//
// Template for WIX Custom Actions written in Javascript.
//
//
// Mon, 23 Nov 2009  10:54
//
// ===================================================================


// http://msdn.microsoft.com/en-us/library/sfw6660x(VS.85).aspx
var Buttons = {
        OkOnly           : 0,
        OkCancel         : 1,
        AbortRetryIgnore : 2,
        YesNoCancel      : 3
};

var Icons = {
        Critical         : 16,
        Question         : 32,
        Exclamation      : 48,
        Information      : 64
};

var MsgKind = {
        Error            : 0x01000000,
        Warning          : 0x02000000,
        User             : 0x03000000,
        Log              : 0x04000000
};

// http://msdn.microsoft.com/en-us/library/aa371254(VS.85).aspx
var MsiActionStatus = {
        None             : 0,
        Ok               : 1, // success
        Cancel           : 2,
        Abort            : 3,
        Retry            : 4, // aka suspend?
        Ignore           : 5  // skip remaining actions; this is not an error.
};


function removeBurn() {
    try {
        _removeBurn();
    }
    catch (exc1) {
        Session.Property("CA_EXCEPTION") = exc1.message ;
        LogException(exc1);
        return MsiActionStatus.Abort;
    }
    return MsiActionStatus.Ok;
}

// Pop a message box.  also spool a message into the MSI log, if it is enabled.
function LogException(exc) {
    var record = Session.Installer.CreateRecord(0);
    record.StringData(0) = "CustomAction: Exception: 0x" + decimalToHexString(exc.number) + " : " + exc.message;
    Session.Message(MsgKind.Error + Icons.Critical + Buttons.btnOkOnly, record);
}


// spool an informational message into the MSI log, if it is enabled.
function LogMessage(msg) {
    var record = Session.Installer.CreateRecord(0);
    record.StringData(0) = "CustomAction:: " + msg;
    Session.Message(MsgKind.Log, record);
}


// popup a msgbox
function AlertUser(msg) {
    var record = Session.Installer.CreateRecord(0);
    record.StringData(0) = msg;
    Session.Message(MsgKind.User + Icons.Information + Buttons.btnOkOnly, record);
}

// Format a number as hex.  Quantities over 7ffffff will be displayed properly.
function decimalToHexString(number) {
    if (number < 0)
        number = 0xFFFFFFFF + number + 1;
    return number.toString(16).toUpperCase();
}

function ensureValue(Result, strKeyPath, Key, Name, objShell){
    if(!Result) {
        // oReg did not provide the result, so we must get it ourselves
        Result = objShell.RegRead("HKLM\\" + strKeyPath + "\\" + Key + "\\" + Name);
        try{
            Result = VBArray(Result).toArray().join();
        } catch (e) {}
    }

    return Result
}

function _removeBurn() {
    var HKEY_CLASSES_ROOT = 0x80000000;
    var HKEY_CURRENT_USER = 0x80000001;
    var HKEY_LOCAL_MACHINE = 0x80000002;
    var HKEY_USERS = 0x80000003;
    var HKEY_PERFORMANCE_DATA = 0x80000004;
    var HKEY_CURRENT_CONFIG = 0x80000005;

    var REG_SZ = 1;
    var REG_EXPAND_SZ = 2;
    var REG_BINARY = 3;
    var REG_DWORD = 4;
    var REG_MULTI_SZ = 7;

    var strKeyPath = "Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall";

    var Values;
    var BundleUpgradeCode;
    var UninstallString;
    var QuietUninstallString;
    var objShell = new ActiveXObject("WScript.Shell");
    var Keys = regGetChildKeys(HKEY_LOCAL_MACHINE, strKeyPath);

    for (j = 0; j < Keys.Names.length; j++){
        BundleUpgradeCode = "";
        UninstallString = "";
        QuietUninstallString = "";
        Values = regGetChildValues(HKEY_LOCAL_MACHINE, strKeyPath + "\\" + Keys.Names[j]);

        for (i = 0; i < Values.Names.length; i++) {
            if ((Values.Types[i] == REG_SZ)|| (Values.Types[i] == REG_MULTI_SZ)) {
                switch(Values.Names[i]) {
                    case "BundleUpgradeCode":
                         BundleUpgradeCode = ensureValue(Values.Results[i], strKeyPath, Keys.Names[j], Values.Names[i], objShell);
                         break;
                    case "UninstallString":
                        UninstallString = ensureValue(Values.Results[i], strKeyPath, Keys.Names[j], Values.Names[i], objShell)
                        break;
                    case "QuietUninstallString":
                        QuietUninstallString = ensureValue(Values.Results[i], strKeyPath, Keys.Names[j], Values.Names[i], objShell);
                        break;
                }
            }
        }

        if(BundleUpgradeCode.toUpperCase() == "{upgrade_code}".toUpperCase()) {
            var command = null;
            if(QuietUninstallString)
                command = QuietUninstallString;
            else if(UninstallString)
                command = UninstallString;

            if(command) {
                objShell.Exec(command);
            }
        }
    }
}

function regGetChildKeys(regRoot, strRegPath){
    var aNames = [];
    var objReg = GetObject("winmgmts://./root/default:StdRegProv");
    var objMethod = objReg.Methods_.Item("EnumKey");
    var objInParam = objMethod.InParameters.SpawnInstance_();
    objInParam.hDefKey = regRoot;
    objInParam.sSubKeyName = strRegPath;
    var objOutParam = objReg.ExecMethod_(objMethod.Name, objInParam);
    switch (objOutParam.ReturnValue) {
      case 0:          // Success
        aNames = (objOutParam.sNames != null) ? objOutParam.sNames.toArray() : [];
        break;
      case 2:        // Not Found
        aNames = [];
        break;
    }
    return {Names: aNames}
}

// Gets names and types of all values under given registry Key
function regGetChildValues(regRoot, strRegPath) {
    var aNames = [];
    var aTypes = [];
    var methods = ["GetStringValue", "GetMultiStringValue"];
    var objReg = GetObject("winmgmts://./root/default:StdRegProv");
    var objMethod = objReg.Methods_.Item("EnumValues");
    var objInParam = objMethod.InParameters.SpawnInstance_();
    objInParam.hDefKey = regRoot;
    objInParam.sSubKeyName = strRegPath;
    var objOutParam = objReg.ExecMethod_(objMethod.Name, objInParam);
    switch (objOutParam.ReturnValue) {
      case 0:          // Success
        aNames = (objOutParam.sNames != null) ? objOutParam.sNames.toArray() : [];
        aTypes = (objOutParam.Types != null) ? objOutParam.Types.toArray() : [];
        break;
      case 2:        // Not Found
        aNames = [];
        break;
    }
    var aResults = [];
    for (i = 0; i < aNames.length; i++) {
        objMethod = objReg.Methods_.Item("GetStringValue");
        objInParam = objMethod.InParameters.SpawnInstance_();
        objInParam.hDefKey = regRoot;
        objInParam.sSubKeyName = strRegPath;
        objInParam.sValueName = aNames[i];
        objOutParam = objReg.ExecMethod_(objMethod.Name, objInParam);
        aResults.push(objOutParam.sValue);
    }
  return { Results: aResults, Names: aNames, Types: aTypes };
}