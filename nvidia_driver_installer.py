import os
import subprocess

UBUNTU = 'Ubuntu'
FEDORA = 'Fedora'
MANJARO = 'Manjaro'
MINT = 'Linux Mint'


def elevate():
    os.system("pkexec python3 $(readlink -f nv*)")


def get_system_name():
    f = open('/usr/lib/os-release', 'r')
    os_data = f.readline()
    f.close()

    if UBUNTU in os_data:
        return UBUNTU
    elif FEDORA in os_data:
        return FEDORA
    elif MANJARO in os_data:
        return MANJARO
    elif MINT in os_data:
        return MINT
    else:
        return 'Unknown'


def exec_bash(command):
    output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if output.returncode != 0:
        print('Failed to execute', command)
        exit(-1)

    return output.stdout.decode('utf-8')


def elevate_privileges():
    output = exec_bash('whoami')

    if output == 'root\n':  # Why '\n'? Because exec_bash(command) returns output with '\n' at the end!
        return True
    else:
        elevate()
        output = exec_bash('whoami')
        if output == 'root\n':
            print('Now I\'m running as root.')
        else:
            exit()


def update_repositories(system_name):
    if system_name == UBUNTU or system_name == MINT:
        subprocess.run(['sudo', 'apt', 'update'])
    elif system_name == FEDORA:
        subprocess.run(['sudo', 'dnf' 'update', '-y'])
    else:
        print("UNSUPPORTED SYSTEM!")
        exit(-1)


def get_available_drivers(system_name):
    if system_name == UBUNTU:
        output = exec_bash(['apt', 'search', '"NVIDIA driver metapackage"'])
        drivers = list()
        for i in range(len(output)):
            if output[i] == 'n' and output[i + 1] == 'v' \
                    and output[i + 2] == 'i' and output[i + 3] == 'd':
                drivers.append(output[i:i + 17])  # 17 - length of nvidia-driver-XXX
        return drivers
    elif system_name == MINT:
        output = exec_bash(['apt', 'search', 'nvidia-driver-'])
        drivers = list()
        for i in range(len(output)):
            if output[i:i + 13] == 'nvidia-driver' and output[i + 18] == ' ':
                drivers.append(output[i:i + 17])
                print('found at pos:', i)
        return drivers

    elif system_name == FEDORA:
        print("Checking RPMFusion-nvidia-nonfree")  # Check for RPMFusion NVIDIA repo, and install it if not found
        exec_bash(['dnf', 'install', 'fedora-workstation-repositories', '-y'])
        exec_bash(['dnf', 'config-manager', '--set-enabled', 'rpmfusion-nonfree-nvidia-driver', '-y'])
        # Now we should have RPMFusion installed and active


def main():
    elevate_privileges()

    print('WARNING! THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, '
          'EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, '
          'FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT '
          'HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, '
          'TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN '
          'THE SOFTWARE.')

    answer = input('Continue? [y/n]\n')

    if answer != 'y':
        print('Quitting...')
        exit(0)

    system_name = get_system_name()

    print('Looks like you\'re using', system_name)

    if system_name == UBUNTU or system_name == MINT:
        print('Let\'s update your repositories!\n')
        update_repositories(system_name)

        print('All right! Let\'s find some nvidia drivers...')
        available_drivers = get_available_drivers(system_name)

        print('Okay. I\'ve found', len(available_drivers), 'of them')

        for i in range(len(available_drivers)):
            print(str(i + 1) + '.' + str(available_drivers[i]))

        print('What driver should I install? Please enter its name')
        selected_driver = int(input()) - 1
        os.system('yes | ' + 'sudo apt install ' + available_drivers[selected_driver])

        print('Removing unnecessary packages...')
        os.system('yes | sudo apt autoremove')

        print('Okay. Installation finished. Please reboot your PC! Would you like to reboot it now? [y/n]')
        answer = input()

        if answer == 'y':
            os.system('reboot')

    elif system_name == FEDORA:
        print('Let\'s update your repositories!\n')

        update_repositories(system_name)

        print("We'll check for the RPMFusion repositories which contain the drivers")

        get_available_drivers(system_name)

        print('What NVIDIA card do you have?:')
        print('Type 1 for recent GeForce/Quadro/Tesla')
        print('Type 2 for legacy GeForce 400/500')
        print('Type 3 for Legacy GeForce 8/9/200/300')
        card_type = int(input())

        # Driver installation
        if card_type == 1:
            exec_bash(['dnf', 'install', 'akmod-nvidia', '-y'])
        elif card_type == 2:  # Possibly broken, no way to test due to missing hardware (aka, I dont have an old GPU)
            exec_bash(['dnf', 'install', 'xorg-x11-drv-nvidia-390xx', 'akmod-nvidia-390xx', '-y'])
        elif card_type == 3:  # Possibly broken, no way to test due to missing hardware (aka, I dont have an old GPU)
            exec_bash(['dnf', 'install', 'xorg-x11-drv-nvidia-340xx', 'akmod-nvidia-340xx', '-y'])

        print("Configuring boot splash(plymouth)")

        # After installing the drivers, you MUST make the drivers start at preboot (after GRUB) so the boot screen
        # displays properly

        exec_bash(['echo', '"options nvidia_drm modeset=1"', '>>', '/etc/modprobe.d/nvidia.conf'])
        exec_bash(['echo',
                   'add_drivers+="nvidia nvidia_modeset nvidia_uvm '
                   'nvidia_drm"\ninstall_items+="/etc/modprobe.d/nvidia.conf"',
                   '>>',
                   '/etc/dracut.conf.d/nvidia.conf'])
        exec_bash(['dracut', '-f'])

        print('Okay. Installation finished. Please reboot your PC! Would you like to reboot your PC now? [y/n]')

        answer = input()

        if answer == 'y':
            os.system('reboot')

    elif system_name == MANJARO:
        # Literally one line of code. Do we need this?
        os.system('mhwd -a pci nonfree 0300')

    print('Thank you for using this software! Made by r1ddle & thonkdifferent')


main()
