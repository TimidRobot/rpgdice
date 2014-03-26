#!/bin/bash
#
# This file was created to assist with troubleshooting the installation of
# requirements on Mac OS 10.9.2 Maverics with Xcode 5.1
#
# Takes ~14 minutes on a MacBook Pro (Retina, 15-inch, Early 2013)


header() {
    for x in {1..80}
    do
        printf "${1:-=}"
    done
    echo
}


pip_install() {
    local _pkg
    _pkg=${1}
    _desc=$(pip search ${_pkg} | awk -F- "/^${_pkg} / {print \$2}")
    printf "${_pkg}"
    if [[ -n "${_desc}" ]]
    then
        _desc=${_desc# }
        echo " - ${_desc}"
    else
        echo
    fi
    header '-'
    if pip freeze | egrep -q "^${_pkg}="
    then
       echo 'Already installed'
    else
        if pip install ${_pkg}
        then
            :  # success no-op
        else
            es=${?}
            echo
            echo "ERROR: ${_pkg} failed with exit status: ${es}"
            exit ${es}
        fi
    fi
    echo
    echo
}


echo 'Confirm gfortran has been installed via brew'
header
if brew list gfortran &>/dev/null
then
    echo 'Confirmed.'
else
    es=${?}
    echo 'Negative.'
    exit ${es}
fi
echo
echo


echo 'Confirm freetype has been installed via brew'
header
if brew list freetype &>/dev/null
then
    echo 'Confirmed.'
else
    es=${?}
    echo 'Negative.'
    exit ${es}
fi
echo
echo


echo 'Add additional freetype include link so headers can be found. Based on:'
echo 'http://stackoverflow.com/questions/20572366/sudo-pip-install-matplotlib-fails-to-find-freetype-headers-os-x-mavericks'
header
ln -sv /usr/local/include/freetype2 /usr/local/include/freetype 2>/dev/null
echo 'Done.'
echo
echo

echo 'Set flags for C extentions compling. Based on:'
echo 'http://stackoverflow.com/questions/22313407/clang-error-unknown-argument-mno-fused-madd-python-package-installation-fa'
header
export ARCHFLAGS='-Wno-error=unused-command-line-argument-hard-error-in-future'
export CFLAGS='-Qunused-arguments -I'
export CPPFLAGS='-Qunused-arguments'
export PKG_CONFIG_PATH='/usr/X11/lib/pkgconfig'
echo 'Done.'
echo
echo


echo 'Install Python packages via pip'
header
echo
echo

# 0 levels of dependencies
for dep in backports.ssl-match-hostname brewer2mpl nose numpy pyparsing pytz \
           scipy six
do
    pip_install ${dep}
done


# 1 level of dependencies
#   patsy
#       numpy
#   python-dateutil
#       six
#   tornado
#       backports.ssl-match-hostname
for dep in patsy python-dateutil tornado
do
    pip_install ${dep}
done


# 2 levels of dependencies
#   matplotlib
#       nose
#       numpy
#       pyparsing
#       python-dateutil
#       tornado
#   pandas
#       numpy
#       python-dateutil
#       six
for dep in matplotlib pandas
do
    pip_install ${dep}
done


# 3 levels of dependencies
#   statsmodels
#       numpy
#       pandas
#       patsy
#       scipy
for dep in statsmodels
do
    pip_install ${dep}
done


# 4 levels of dependencies
#   gglplot
#       brewer2mpl
#       matplotlib
#       numpy
#       pandas
#       patsy
#       scipy
#       statsmodels
pip_install ggplot
