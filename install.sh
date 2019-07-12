add_repos(){
  echo "Adding repos"
  echo "... nothign to see here! "
  echo "============"
}

update(){
# update apt
    echo "Updating apt-get"
    echo "================"
    echo " "

    sudo apt-get update -y
}

package_check() {
  # Loop through each of our packages that should be installed on the system. If
  # not yet installed, it should be added to the array of packages to install.
  local pkg
  local package_version

  for pkg in "${apt_package_check_list[@]}"; do
    package_version=$(dpkg -s "${pkg}" 2>&1 | grep 'Version:' | cut -d " " -f 2)
    if [[ -n "${package_version}" ]]; then
      space_count="$(expr 20 - "${#pkg}")" #11
      pack_space_count="$(expr 30 - "${#package_version}")"
      real_space="$(expr ${space_count} + ${pack_space_count} + ${#package_version})"
      printf " * $pkg %${real_space}.${#package_version}s ${package_version}\n"
    else
      echo " *" $pkg [not installed]
      apt_package_install_list+=($pkg)
    fi
  done


}

pip_installs(){
  sudo pip install --upgrade google-api-python-client
  sudo pip install --upgrade oauth2client
  sudo pip install --upgrade mpg321
}

install(){
  # update apt
    echo "Updating apt-get"
    echo "================"
    echo " "

    apt-get install -y ${apt_package_install_list[@]}
}

apt_package_install_list=()
apt_package_check_list=(
  python-pil
  python-pil.imagetk
  python-gdata
  imagemagick
  cups
  python-cups
)

add_repos
update
package_check
install
pip_installs