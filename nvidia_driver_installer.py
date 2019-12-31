import subprocess
import os
import re

UBUNTU = 'Ubuntu'
FEDORA = 'Fedora'
MANJARO = 'Manjaro'

def get_system_name():
    try:
        output = execute_shell_command(['lsb_release', '-a'])
        if UBUNTU in output:
            return UBUNTU
        elif FEDORA in output:
            return FEDORA
        elif MANJARO in output:
            return MANJARO
    except FileNotFoundError:
        print("lsb_release not found. If you are on Fedora, install the redhat-lsb-core package")


def execute_shell_command(command):
    output = subprocess.check_output(command, encoding='UTF-8')
    return output


def is_running_as_root():
    output = execute_shell_command('whoami')

    if output == 'root\n':  # Why '\n'? Because execute_shell_command(command) returns output with '\n' at the end!
        return True
    else:
        return False


def update_repositories(system_name):
    if system_name == UBUNTU:
        os.system('sudo apt update')
    elif system_name == FEDORA:
        os.system('sudo dnf update')
    else:
        print("UNSUPPORTED SYSTEM!")
        exit()


def get_available_drivers(system_name):
    if system_name == UBUNTU:
        output = execute_shell_command(['apt','search', "NVIDIA driver metapackage"])
        drivers = []
        for i in range(len(output)):
            if output[i] == 'n' and output[i + 1] == 'v' \
            and output[i + 2] == 'i' and output[i + 3] == 'd':
                drivers.append(output[i:i + 17])  # 17 - length of nvidia-driver-XXX
        return drivers
    elif system_name == FEDORA:
        print("Checking RPMFusion-nvidia-nonfree")  # Check for RPMFusion NVIDIA repo, and install it if not found
        execute_shell_command(["dnf", "install", "fedora-workstation-repositories"])
        execute_shell_command(["dnf", "config-manager", "--set-enabled","rpmfusion-nonfree-nvidia-driver"])
        # Now we should have RPMFusion installed and active



def main():
    is_root = is_running_as_root()
    print("Running as root?: ", is_root)

    if not is_root:
        print("Error! Please run this program as root!")
        exit(-1)
    else:
        print('Good! Program is running as root!')

    print('WARNING! THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, '
    'EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, '
    'FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT '
    'HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, '
    'TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.')

    answer = input('Continue? [y/n]\n')

    if answer != 'y':
        print('Quitting...')
        exit(0)

    system_name = get_system_name()

    if system_name == UBUNTU:
        print('Looks like you\'ve installed Ubuntu\n\n')

        print('Let\'s update your repositories!\n\n')
        update_repositories(system_name)

        print('All right! Let\'s find some nvidia drivers...')
        available_drivers = get_available_drivers(system_name)

        print('Okay. I\'ve found', len(available_drivers), 'of them')

        for i in range(len(available_drivers)):
            print(str(i + 1) + '.' + str(available_drivers[i]))

        print('What driver should I install? Please enter its name')
        selected_driver = int(input()) - 1
        os.system('yes | ' + 'sudo apt install ' + available_drivers[selected_driver])

        print('Removing unnecesessary packages...')
        os.system('yes | sudo apt autoremove')

        print('Okay. Installation finished. Please reboot your PC! Would you like to reboot your PC now? [y/n]')
        answer = input()

        if answer == 'y':
            os.system('reboot')

    elif system_name == FEDORA:
        print('Looks like you\'re using Fedora.')
        print('Let\'s update your repositories!\n\n')

        update_repositories(system_name)

        print("We'll check for the RPMFusion repositories wich contain the drivers")

        print('What NVIDIA card do you have?:')
        print('Type 1, for recent GeForce/Quadro/Tesla')
        print('Type 2 for legacy GeForce 400/500')
        print('Type 3 for Legacy GeForce 8/9/200/300')
        card_type = int(input())

        # Driver instalation
        if card_type == 1:
            execute_shell_command(["dnf", "install", "akmod-nvidia"])
        elif card_type == 2:  # Possibly broken, no way to test due to missing hardware (aka, I dont have an old GPU)
            execute_shell_command(["dnf", "install", "xorg-x11-drv-nvidia-390xx","akmod-nvidia-390xx"])
        elif card_type == 3:  # Possibly broken, no way to test due to missing hardware (aka, I dont have an old GPU)
            execute_shell_command(["dnf", "install", "xorg-x11-drv-nvidia-340xx","akmod-nvidia-340xx"])

        print("Configuring boot splash(plymouth)")

        # After installing the drivers, you MUST make the drivers start at preboot (after GRUB) so the boot screen displays properly

        execute_shell_command(["echo", "\"options nvidia_drm modeset=1\" ", ">>", "/etc/modprobe.d/nvidia.conf"])
        execute_shell_command(["echo",
                               "add_drivers+=\"nvidia nvidia_modeset nvidia_uvm nvidia_drm\"\ninstall_items+=\"/etc/modprobe.d/nvidia.conf\"", 
                               ">>",
                               "/etc/dracut.conf.d/nvidia.conf"])
        execute_shell_command(["dracut", "-f"])

        print('Okay. Installation finished. Please reboot your PC! Would you like to reboot your PC now? [y/n]')

        answer = input()

        if answer == 'y':
            os.system('reboot')

    print('Thank you for using this software! Made by r1ddle & thonkdifferent')


main()
