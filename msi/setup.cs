//css_nuget WixSharp.bin;
//css_ref System.Core.dll;
using System;
using WixSharp;
using WixSharp.Bootstrapper;
using System.Text.RegularExpressions;
using io = System.IO;

class Script
{
    static public void Main(string[] args)
    {
        string pName = "{project-name}";
        Project project = new Project(pName,
            new Dir(new Id("INSTALL_DIR"), @"{install-dir}",
                new Files(@"dist\vnc_gui\*.*")),
            new Dir(@"{shortcut-location}",
                    new ExeFileShortcut(pName, "[INSTALL_DIR]{shortcut-target}", "")))
        { InstallScope = InstallScope.perMachine };

        project.Platform = Platform.x64;
        project.Version = new Version(io.File.ReadAllText(@"VERSION"));
        project.GUID = new Guid("{upgrade-code}");
        project.MajorUpgradeStrategy = MajorUpgradeStrategy.Default;

        string msi = project.BuildMsi();

        var bootstrapper = new Bundle(pName,
            new MsiPackage(msi) { DisplayInternalUI = false });

        bootstrapper.Version = project.Version;
        bootstrapper.UpgradeCode = (Guid)project.GUID;
        bootstrapper.Application.LicensePath = "LICENSE.txt";
        bootstrapper.Application.AttributesDefinition = "SuppressOptionsUI=yes";
        bootstrapper.OutFileName = io.Path.GetFileNameWithoutExtension(msi);

        // bootstrapper.PreserveTempFiles = true;

        io.File.Copy(io.Path.GetFileNameWithoutExtension(bootstrapper.Application.LicensePath), bootstrapper.Application.LicensePath);
        io.File.WriteAllText(bootstrapper.Application.LicensePath,
                          Regex.Replace(io.File.ReadAllText(bootstrapper.Application.LicensePath),
                                        @"\r\n?|\n", Environment.NewLine));

        bootstrapper.Build();

        if (io.File.Exists(msi))
            io.File.Delete(msi);

        if (io.File.Exists(bootstrapper.Application.LicensePath))
            io.File.Delete(bootstrapper.Application.LicensePath);
    }
}