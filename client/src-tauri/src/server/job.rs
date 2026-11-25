//! Un Job Object con KILL_ON_JOB_CLOSE: el server muere con la ventana aunque la app se cierre mal (D-2).
// cspell:ignore Toolhelp SNAPTHREAD THREADENTRY
use std::os::windows::io::AsRawHandle;
use std::process::Child;

use windows::Win32::Foundation::{CloseHandle, HANDLE};
use windows::Win32::System::Diagnostics::ToolHelp::{
    CreateToolhelp32Snapshot, Thread32First, Thread32Next, TH32CS_SNAPTHREAD, THREADENTRY32,
};
use windows::Win32::System::JobObjects::{
    AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
    SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
};
use windows::Win32::System::Threading::{OpenThread, ResumeThread, THREAD_SUSPEND_RESUME};

pub struct KillOnClose(HANDLE);

// El HANDLE solo se usa para cerrarlo en Drop; el Job no se comparte entre hilos.
unsafe impl Send for KillOnClose {}
unsafe impl Sync for KillOnClose {}

impl KillOnClose {
    pub fn assign(child: &Child) -> windows::core::Result<Self> {
        let mut info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        unsafe {
            let job = CreateJobObjectW(None, None)?;
            // Desde aquí, el Drop cierra el handle si un `?` de abajo sale antes del Ok.
            let owned = Self(job);
            let size = std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32;
            SetInformationJobObject(
                job,
                JobObjectExtendedLimitInformation,
                &info as *const _ as *const _,
                size,
            )?;
            AssignProcessToJobObject(job, HANDLE(child.as_raw_handle()))?;
            Ok(owned)
        }
    }
}

/// Pone en marcha los hilos de un proceso que arrancó suspendido, ya dentro del Job.
pub fn resume(child: &Child) -> windows::core::Result<()> {
    let pid = child.id();
    unsafe {
        let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)?;
        let result = resume_threads(snapshot, pid);
        CloseHandle(snapshot)?;
        result
    }
}

/// Reanuda cada hilo de `pid` que aparece en la instantánea de hilos.
unsafe fn resume_threads(snapshot: HANDLE, pid: u32) -> windows::core::Result<()> {
    unsafe {
        let mut entry = THREADENTRY32 {
            dwSize: std::mem::size_of::<THREADENTRY32>() as u32,
            ..Default::default()
        };
        let mut more = Thread32First(snapshot, &mut entry).is_ok();
        while more {
            if entry.th32OwnerProcessID == pid {
                let thread = OpenThread(THREAD_SUSPEND_RESUME, false, entry.th32ThreadID)?;
                let previous = ResumeThread(thread);
                let _ = CloseHandle(thread);
                if previous == u32::MAX {
                    return Err(windows::core::Error::from_thread());
                }
            }
            more = Thread32Next(snapshot, &mut entry).is_ok();
        }
    }
    Ok(())
}

impl Drop for KillOnClose {
    fn drop(&mut self) {
        unsafe {
            let _ = CloseHandle(self.0);
        }
    }
}
