import logging

from libvmi import LibvmiError, X86Reg, AccessContext, TranslateMechanism


class RawThread:

    def __init__(self, vmi, id):
        self.log = logging.getLogger(__class__.__name__)
        self.vmi = vmi
        self.id = id
        self.vcpu_id = self.id - 1
        # TODO reply contains invalid digit
        self.name = "0"

    def is_alive(self):
        # always alive, it's a VCPU
        return True

    def read_registers(self):
        self.log.debug('%s: read registers', self.id)
        return self.vmi.get_vcpuregs(self.vcpu_id)


class RawDebugContext:

    def __init__(self, vmi):
        self.log = logging.getLogger(__class__.__name__)
        self.vmi = vmi
        # create threads
        self.threads = []
        for i in range(0, self.vmi.get_num_vcpus()):
            self.threads.append(RawThread(self.vmi, i+1))
        # default thread: all threads
        self.cur_tid = -1

    def attach(self):
        self.log.info('attaching on %s', self.vmi.get_name())
        self.vmi.pause_vm()

    def detach(self):
        logging.info('detaching from %s', self.vmi.get_name())
        try:
            self.vmi.resume_vm()
        except LibvmiError:
            # already in running state
            pass

    def get_dtb(self):
        # get current CR3
        return self.vmi.get_vcpu_reg(X86Reg.CR3.value, 0)

    def get_access_context(self, address):
        return AccessContext(TranslateMechanism.PROCESS_DTB,
                             addr=address, dtb=self.get_dtb())

    def get_thread(self, tid=None):
        if not tid:
            tid = self.cur_tid
        if tid == -1 or tid == 0:
            # -1: indicate all threads
            # 0: pick any thread
            # return first one for now
            return self.list_threads()[0]
        found = [thread for thread in self.list_threads() if thread.id == tid]
        if not found:
            self.log.warning('Cannot find thread ID %s', tid)
            return None
        if len(found) > 1:
            self.log.warning('Multiple threads sharing same id')
        return found[0]

    def list_threads(self):
        return self.threads

    def get_current_thread(self):
        return self.threads[self.cur_tid_idx]
