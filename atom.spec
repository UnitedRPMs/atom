# This spec file is a rework/mix of other spec files (for compatiblity) PKGBUILDs and EBUILDs, and love for all to share. available from
#  [1] https://aur.archlinux.org/packages/atom-editor-bin/
#  [2] https://github.com/helber/fedora-specs

%{?nodejs_find_provides_and_requires}
%global arch %(test $(rpm -E%?_arch) = x86_64 && echo "x64" || echo "ia32")
%global debug_package %{nil}
%global _hardened_build 1
%global __provides_exclude_from %{_datadir}/%{name}/node_modules
%global __requires_exclude_from %{_datadir}/%{name}/node_modules
%global __provides_exclude_from %{_datadir}/%{name}/
%global __requires_exclude_from %{_datadir}/%{name}/
%global __requires_exclude (npm|libnode)

# globals for node and nodewebkit (nw)
# As recommendation check the specific version of node and electron in its ".travis.yml" and "package.json" for a successful build.
%global nodev 6.9.4

#Electron version
%global elev 1.3.15

#defining architectures
%ifarch x86_64
%global platform linux64
%global archnode linux-x64
%else
%global platform linux32
%global archnode linux-x86
%endif

# commit
%global _commit b96141905f5f40b6c939fca8f64a23e60b785af5
%global _shortcommit %(c=%{_commit}; echo ${c:0:7})

%bcond_without no_bin

Name:    atom
Version: 1.22.1
Release: 1%{?gver}%{?dist}
Summary: A hack-able text editor for the 21st century

Group:   Applications/Editors
License: MIT
URL:     https://atom.io/

%if %{with no_bin}
Source0: https://github.com/atom/atom/archive/%{_commit}/%{name}-%{_shortcommit}.tar.gz
%else
Source0: https://atom-installer.github.com/v%{version}/atom-amd64.deb
%endif
# Sorry but we need a specific node, npm and electron for compatibility
Source4: https://nodejs.org/dist/v%{nodev}/node-v%{nodev}-%{archnode}.tar.gz
# Source5: https://github.com/electron/electron/releases/download/v%{elev}/electron-v%{elev}-%{archnode}.zip

Patch0:  atom-python.patch
Patch1:  startupwmclass.patch
Patch2:  rpm_build.patch
ExclusiveArch: %{nodejs_arches} noarch

BuildRequires: git
BuildRequires: libtool 
BuildRequires: unzip 
BuildRequires: oniguruma-devel 
BuildRequires: python2-devel 
BuildRequires: libsecret-devel 
BuildRequires: libX11-devel 
BuildRequires: libxkbfile-devel
BuildRequires: gnome-keyring
BuildRequires: curl
BuildRequires: xz tar git
# new build requires
BuildRequires: gtk2
BuildRequires: libXScrnSaver
BuildRequires: GConf2
BuildRequires: alsa-lib
 
Requires: desktop-file-utils
Requires: gvfs
Requires: ctags
Requires: http-parser
Requires: zsh

%description
Atom is a text editor that's modern, approachable, yet hack-able to the core
- a tool you can customize to do anything but also use productively without
ever touching a config file.


%prep

%if %{with no_bin}
%setup -q -n %name-%{_commit} -a4 
%patch2 -p0
mkdir -p electron-v%{elev}-%{archnode}
#unzip %{S:5} -d electron-v%{elev}-%{archnode}/
sed -i 's|Exec=<%= installDir %>/share/|Exec=/usr/share/atom/atom %F|g' resources/linux/atom.desktop.in
sed -i 's|Icon=<%= iconPath %>|Icon=atom|g' resources/linux/atom.desktop.in
%else
# extract data from the deb package
install -dm 755 %{_builddir}/%{name}-%{version}
ar x %{SOURCE0} 
if [ -f data.tar.xz ]; then
tar xJf data.tar.xz -C %{_builddir}/%{name}-%{version}
elif [ -f data.tar.gz ]; then 
tar xmzvf data.tar.gz -C %{_builddir}/%{name}-%{version}
fi
%setup -T -D %{name}-%{version}
%patch0 -p1
%patch1 -p1
sed -i 's|env PYTHON=python2 GTK_IM_MODULE= QT_IM_MODULE= XMODIFIERS= /usr/share/atom/atom|/usr/bin/atom|' usr/share/applications/atom.desktop
chmod -R g-w usr
%endif

%build

%if %{with no_bin}

# get nvm

git clone git://github.com/creationix/nvm.git ~/nvm

# activate nvm

echo "source ~/nvm/nvm.sh" >> ~/.bashrc

source ~/.bashrc
nvm install 6.9.4
nvm use 6.9.4

export PATH=$PATH:$PWD/node-v%{nodev}-%{archnode}/bin:$PWD/electron-v%{elev}-%{archnode}/:/usr/bin/
$PWD/node-v%{nodev}-%{archnode}/bin/npm config set python /usr/bin/python2 
$PWD/node-v%{nodev}-%{archnode}/bin/npm cache clean
$PWD/node-v%{nodev}-%{archnode}/bin/npm config set registry http://registry.npmjs.org/
$PWD/node-v%{nodev}-%{archnode}/bin/npm install npm@5.3.0
%endif


%install

%if %{with no_bin}
install -dm 755 %{buildroot}/usr
export PATH=$PATH:$PWD/node-v%{nodev}-%{archnode}/bin:$PWD/electron-v%{elev}-%{archnode}/:/usr/bin/
pushd script
./build --install=%{buildroot}/usr 
popd
# copy over icons in sizes that most desktop environments like
  for size in 16 24 32 48 64 128 256 512 1024; do
    install -D -m 644 resources/app-icons/stable/png/${size}.png \
            %{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps/atom.png
  done
sed -i 's|file.file<%= appFileName %>/atom||g' %{buildroot}/%{_datadir}/applications/%{name}.desktop
%else

# Make destiny directories
install -dm 755 %{buildroot}/%{_libdir} \
%{buildroot}/%{_bindir} 

cp -rf usr/ %{buildroot}/

%endif


%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
/usr/bin/update-desktop-database &>/dev/null ||:

%postun
if [ $1 -eq 0 ]; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null ||:
    /usr/bin/gtk-update-icon-cache -f -t -q %{_datadir}/icons/hicolor ||:
fi
/usr/bin/update-desktop-database &>/dev/null ||:

%posttrans
/usr/bin/gtk-update-icon-cache -f -t -q %{_datadir}/icons/hicolor ||:

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%exclude %{_bindir}/apm
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%if %{with no_bin}
%doc README.md CONTRIBUTING.md docs/
%license LICENSE.md
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%else
%{_bindir}/apm
%{_docdir}/atom/copyright
%exclude %{_datadir}/lintian/
%{_datadir}/pixmaps/%{name}.png
%endif

%changelog

* Sun Nov 19 2017 David Va <davidva AT tutanota DOT com> 1.22.1-1
- Updated to 1.22.1

* Sat Nov 11 2017 David Va <davidva AT tutanota DOT com> 1.22.0-1
- Updated to 1.22.0

* Sat Oct 14 2017 David Va <davidva AT tutanota DOT com> 1.21.1-2
- Updated to current commit stable

* Fri Oct 13 2017 David Va <davidva AT tutanota DOT com> 1.21.1-1
- Updated to 1.21.1

* Thu Oct 05 2017 David Va <davidva AT tutanota DOT com> 1.21.0-1
- Updated to 1.21.0

* Mon Oct 02 2017 David Va <davidva AT tutanota DOT com> 1.20.1-1
- Updated to 1.20.1

* Sun Aug 13 2017 David Va <davidva AT tutanota DOT com> 1.19.0-1
- Updated to 1.19.0-1

* Wed Aug 02 2017 David Va <davidva AT tutanota DOT com> 1.18.0-2
- Rebuilt using nvm

* Mon Jul 24 2017 David Va <davidva AT tutanota DOT com> 1.18.0-1
- New structure

* Sun Apr 30 2017 "UnitedRPMs autorebuilder <unitedrpms@protonmail.com>" - 1.15.0-2.git3e457f3
- rebuilt

* Sat Mar 11 2017 mosquito <sensor.wen@gmail.com> - 1.15.0-1.git3e457f3
- Release 1.15.0
* Sat Feb 11 2017 mosquito <sensor.wen@gmail.com> - 1.14.1-2.gita49cd59
- Fix restart
- Use system ctags for symbols-view
* Sat Feb 11 2017 mosquito <sensor.wen@gmail.com> - 1.14.1-1.gita49cd59
- Release 1.14.1
- Move script to script-old, https://github.com/atom/atom/commit/6856534
* Tue Jan 17 2017 mosquito <sensor.wen@gmail.com> - 1.13.0-1.gita357b4d
- Release 1.13.0
* Fri Jan 13 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-3.git4573089
- Add ctags-config file for symbols-view
* Sun Jan  8 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-2.git4573089
- Fix jump to method causes error
* Tue Jan  3 2017 mosquito <sensor.wen@gmail.com> - 1.12.7-1.git4573089
- Release 1.12.7
* Thu Dec  1 2016 mosquito <sensor.wen@gmail.com> - 1.12.6-1.git5a3d615
- Release 1.12.6
* Thu Oct 20 2016 mosquito <sensor.wen@gmail.com> - 1.11.2-1.git0ecc150
- Release 1.11.2
* Thu Oct 20 2016 mosquito <sensor.wen@gmail.com> - 1.11.1-2.git099ffef
- Fix cannot find shortest_path_tree module
* Sat Oct 15 2016 mosquito <sensor.wen@gmail.com> - 1.11.1-1.git099ffef
- Release 1.11.1
- Replace Grunt-based build system. See https://github.com/atom/atom/pull/12410
* Mon Sep 26 2016 mosquito <sensor.wen@gmail.com> - 1.10.2-1.git3ae8b29
- Release 1.10.2
* Fri Sep  2 2016 mosquito <sensor.wen@gmail.com> - 1.10.0-1.git4f3b013
- Release 1.10.0
* Sun Aug  7 2016 mosquito <sensor.wen@gmail.com> - 1.9.6-1.gite0801e7
- Release 1.9.6
* Sat Aug  6 2016 mosquito <sensor.wen@gmail.com> - 1.9.5-1.git4c1a1e3
- Release 1.9.5
* Fri Aug  5 2016 mosquito <sensor.wen@gmail.com> - 1.9.4-1.gita222879
- Release 1.9.4
* Tue Aug  2 2016 mosquito <sensor.wen@gmail.com> - 1.9.0-1.git59b62a2
- Release 1.9.0
* Fri Jun 17 2016 mosquito <sensor.wen@gmail.com> - 1.8.0-2.gitf89b273
- Build for electron 0.37.8
* Thu Jun  9 2016 mosquito <sensor.wen@gmail.com> - 1.8.0-1.gitf89b273
- Release 1.8.0
- Build for electron 1.2.2
- Fix tree-view does not work
  https://github.com/FZUG/repo/issues/120
* Tue May 31 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-4.git6bed3e5
- Use node-gyp@3.0.3 for el7, system node-gyp doesn't support
  the if-else conditions syntax
  See https://github.com/JCMais/node-libcurl/issues/56
* Tue May 31 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-3.git6bed3e5
- Remove --build-dir option
- Update to settings-view@0.238.0
- Fix height error on install page
  https://github.com/FZUG/repo/issues/116
* Mon May 30 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-2.git6bed3e5
- Fix settings-view dont work
  https://github.com/FZUG/repo/issues/114
* Thu May 26 2016 mosquito <sensor.wen@gmail.com> - 1.7.4-1.git6bed3e5
- Release 1.7.4
- Build for electron 1.2.0
- Build nodegit 0.12.2 from source code
- Add BReq libtool and git
- Update node 0.12 for fedora 23
* Thu May 26 2016 mosquito <sensor.wen@gmail.com> - 1.7.3-2.git1b3da6b
- Fix spell-check dont work
  https://github.com/FZUG/repo/issues/110
* Fri Apr 29 2016 mosquito <sensor.wen@gmail.com> - 1.7.3-1.git1b3da6b
- Release 1.7.3
- Build for electron 0.37.7
- Remove reduplicate CSP header
* Tue Apr 19 2016 mosquito <sensor.wen@gmail.com> - 1.7.2-1.git1969903
- Release 1.7.2
* Sat Apr 16 2016 mosquito <sensor.wen@gmail.com> - 1.7.1-1.git5dda304
- Release 1.7.1
* Wed Apr 13 2016 mosquito <sensor.wen@gmail.com> - 1.7.0-1.git1e7dc02
- Release 1.7.0
- Update nodegit 0.12.2 for electron 0.37.5
- Fix nodegit build error for node 0.10
* Tue Apr 12 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-3.git42d7c40
- Rebuild for electron 0.37.5
* Wed Apr  6 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-2.git42d7c40
- Rebuild for electron 0.37.4
- Set CSP header to allow load images
- Use ATOM_ELECTRON_URL instead of npm_config_disturl
* Sun Apr  3 2016 mosquito <sensor.wen@gmail.com> - 1.6.2-1.git42d7c40
- Release 1.6.2
* Wed Mar 30 2016 mosquito <sensor.wen@gmail.com> - 1.6.1-1.gitcd9b7d3
- Release 1.6.1
- Remove BReq nodejs, libgnome-keyring-devel, git-core
- Replace Req http-parser to desktop-file-utils
* Tue Mar 29 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-3.git01c7777
- Fixes not found mime.types file
* Mon Mar 21 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-2.git01c7777
- Fixes not found nodegit.node module
- Rewrite install script
* Mon Mar 21 2016 mosquito <sensor.wen@gmail.com> - 1.6.0-1.git01c7777
- Release 1.6.0
* Sun Mar 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-3.gitb8cc0b4
- Fixes renderer path
* Sat Mar 12 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-2.gitb8cc0b4
- rebuild for electron 0.36.11
* Sat Mar  5 2016 mosquito <sensor.wen@gmail.com> - 1.5.4-1.gitb8cc0b4
- Release 1.5.4
* Sun Feb 14 2016 mosquito <sensor.wen@gmail.com> - 1.5.3-2.git3e71894
- The package is split into atom, nodejs-atom-package-manager and electron
- Use system apm and electron
- Not generated asar file
- Remove exception-reporting and metrics dependencies from package.json
- Remove unnecessary files
* Sat Feb 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.3-1.git3e71894
- Release 1.5.3
* Sat Feb 13 2016 mosquito <sensor.wen@gmail.com> - 1.5.2-1.git05731e3
- Release 1.5.2
* Fri Feb 12 2016 mosquito <sensor.wen@gmail.com> - 1.5.1-1.git88524b1
- Release 1.5.1
* Fri Feb  5 2016 mosquito <sensor.wen@gmail.com> - 1.4.3-1.git164201e
- Release 1.4.3
* Wed Jan 27 2016 mosquito <sensor.wen@gmail.com> - 1.4.1-2.git2cf2ccb
- Fix https://github.com/FZUG/repo/issues/64
* Tue Jan 26 2016 mosquito <sensor.wen@gmail.com> - 1.4.1-1.git2cf2ccb
- Release 1.4.1
* Sun Jan 17 2016 mosquito <sensor.wen@gmail.com> - 1.4.0-1.gite0dbf94
- Release 1.4.0
* Sun Dec 20 2015 mosquito <sensor.wen@gmail.com> - 1.3.2-1.git473e885
- Release 1.3.2
* Sat Dec 12 2015 mosquito <sensor.wen@gmail.com> - 1.3.1-1.git3937312
- Release 1.3.1
* Thu Nov 26 2015 mosquito <sensor.wen@gmail.com> - 1.2.4-1.git05ef4c0
- Release 1.2.4
* Sat Nov 21 2015 mosquito <sensor.wen@gmail.com> - 1.2.3-1.gitfb5b1ba
- Release 1.2.3
* Sat Nov 14 2015 mosquito <sensor.wen@gmail.com> - 1.2.1-1.git7e902bc
- Release 1.2.1
* Wed Nov 04 2015 mosquito <sensor.wen@gmail.com> - 1.1.0-1.git402f605
- Release 1.1.0
* Thu Sep 17 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.13-1
- Change lib to libnode
* Tue Sep 01 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.10-1
- Release 1.0.10
* Thu Aug 27 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.8-1
- Clean and test spec for epel, centos and fedora
- Release 1.0.8
* Tue Aug 11 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.6-1
- Release 1.0.6
* Thu Aug 06 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.5-1
- Release 1.0.5
* Wed Jul 08 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.1-1
- Release 1.0.1
* Thu Jun 25 2015 Helber Maciel Guerra <helbermg@gmail.com> - 1.0.0-1
- Release 1.0.0
* Wed Jun 10 2015 Helber Maciel Guerra <helbermg@gmail.com> - 0.208.0-1
- Fix atom.desktop
* Tue Jun 09 2015 Helber Maciel Guerra <helbermg@gmail.com> - 0.207.0-1
- Fix desktop icons and some rpmlint.
* Fri Oct 31 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.141.0-1
- release 0.141.0
* Thu Oct 23 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.139.0-1
- release 0.139.0
* Wed Oct 15 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.137.0-2
- release 0.137.0
* Tue Oct 07 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.136.0-1
- release 0.136.0
* Tue Sep 30 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.133.0-2
- Build OK
* Fri Aug 22 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.123.0-2
- Change package name to atom.
* Thu Aug 21 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.123.0-1
- RPM package is just working.
* Sat Jul 26 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.119.0-1
- Try without nodejs.
* Tue Jul 01 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.106.0-1
- Try new version
* Sun May 25 2014 Helber Maciel Guerra <helbermg@gmail.com> - 0.99.0
- Initial package
