
// we may have a problem with escaped quotes
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

var strKeyPath = 'Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall';

var Values;
var BundleUpgradeCode;
var UninstallString;
var QuietUninstallString;
var objShell = WScript.CreateObject("WScript.Shell");
var Keys = regGetChildKeys(HKEY_LOCAL_MACHINE, strKeyPath);

for (j = 0; j < Keys.Names.length; j++){
    BundleUpgradeCode = '';
    UninstallString = '';
    QuietUninstallString = '';
    Values = regGetChildValues(HKEY_LOCAL_MACHINE, strKeyPath + "\\" + Keys.Names[j]);

    for (i = 0; i < Values.Names.length; i++) {
        if ((Values.Types[i] == REG_SZ)|| (Values.Types[i] == REG_MULTI_SZ)) {
            if(!Values.Results[i]) {
                // oReg did not provide the result, so we must get it ourselves
                Values.Results[i] = objShell.RegRead("HKLM\\" + strKeyPath + "\\" + Keys.Names[j] + "\\" + Values.Names[i]);
                try{
                    Values.Results[i] = VBArray(Values.Results[i]).toArray().join();
                } catch (e) {}
            }

            switch(Values.Names[i]) {
                case "BundleUpgradeCode":
                     BundleUpgradeCode = Values.Results[i];
                     break;
                case "UninstallString":
                    UninstallString = Values.Results[i];
                    break;
                case "QuietUninstallString":
                    QuietUninstallString = Values.Results[i];
                    break;
            }
        }
    }

    if(BundleUpgradeCode.toUpperCase() == "%UPGRADE_CODE%".toUpperCase()) {
        var command = null;
        if(QuietUninstallString)
            command = QuietUninstallString;
        else if(UninstallString)
            command = UninstallString;

        if(command) {
            WScript.Exec(command);
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