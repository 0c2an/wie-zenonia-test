from pathlib import Path

svc = Path('wie-lgt/src/runtime/svc_ids.rs')
text = svc.read_text(encoding='utf-8')

old = "    SelectRecord = 0x199,\n    Unk8 = 0x1a0,"
new = "\n".join([
    "    SelectRecord = 0x199,",
    "    // Experimental LGT database slot 12 used by Zenonia 1.",
    "    ListDatabases = 0x19c,",
    "    Unk8 = 0x1a0,",
])
if old not in text:
    raise SystemExit('Could not find enum insertion point for ListDatabases')
text = text.replace(old, new, 1)

old = "            0x199 => Self::SelectRecord,\n            0x1a0 => Self::Unk8,"
new = "\n".join([
    "            0x199 => Self::SelectRecord,",
    "            0x19c => Self::ListDatabases,",
    "            0x1a0 => Self::Unk8,",
])
if old not in text:
    raise SystemExit('Could not find SVC mapping insertion point for ListDatabases')
text = text.replace(old, new, 1)

# This LGT binary uses stdlib import 0x415 with the classic memset(dst, value, len) ABI.
old = "    Memcpy = 0x414,\n    Memset = 0x418,"
new = "\n".join([
    "    Memcpy = 0x414,",
    "    MemsetLegacy = 0x415,",
    "    Memset = 0x418,",
])
if old not in text:
    raise SystemExit('Could not find stdlib enum insertion point for 0x415')
text = text.replace(old, new, 1)
svc.write_text(text, encoding='utf-8')

wipi = Path('wie-lgt/src/runtime/wipi_c.rs')
text = wipi.read_text(encoding='utf-8')
old = "        WIPICSvcId::SelectRecord => database::select_record.into_body(),\n        WIPICSvcId::Unk8 => database::exists_database.into_body(),"
new = "\n".join([
    "        WIPICSvcId::SelectRecord => database::select_record.into_body(),",
    "        WIPICSvcId::ListDatabases => database::list_databases.into_body(),",
    "        WIPICSvcId::Unk8 => database::exists_database.into_body(),",
])
if old not in text:
    raise SystemExit('Could not find dispatch insertion point for ListDatabases')
text = text.replace(old, new, 1)

old = "\n".join([
    "async fn unk4(_context: &mut dyn WIPICContext, a0: u32, a1: u32, a2: u32, a3: u32) -> Result<u32> {",
    '    tracing::warn!("stub unk4({a0:#x}, {a1:#x}, {a2:#x}, {a3:#x})");',
    "",
    "    Ok(0)",
    "}",
])
new = "\n".join([
    "async fn unk4(context: &mut dyn WIPICContext, a0: u32, a1: u32, a2: u32, a3: u32) -> Result<u32> {",
    '    tracing::warn!("experimental LGT 0x12d fs-info shim({a0:#x}, {a1:#x}, {a2:#x}, {a3:#x})");',
    "",
    '    let path = b"/L";',
    "    let path_ptr = context.alloc_raw((path.len() + 1) as u32)?;",
    "    write_null_terminated_string_bytes(context, path_ptr, path)?;",
    "",
    "    let info_ptr = context.alloc_raw(16)?;",
    "    context.write_bytes(info_ptr, &[0u8; 16])?;",
    "    write_generic(context, info_ptr, path_ptr)?;",
    "",
    "    Ok(info_ptr)",
    "}",
])
if old not in text:
    raise SystemExit('Could not find LGT unk4/0x12d stub')
text = text.replace(old, new, 1)
wipi.write_text(text, encoding='utf-8')

stdlib = Path('wie-lgt/src/runtime/stdlib.rs')
text = stdlib.read_text(encoding='utf-8')
old = "            x if x == StdlibSvcId::Memcpy as u32 => EmulatedFunction::call(&stdlib::memcpy, core, &mut ()).await?.write(core, lr),\n            x if x == StdlibSvcId::Memset as u32 => EmulatedFunction::call(&stdlib::memset, core, &mut ()).await?.write(core, lr),"
new = "\n".join([
    "            x if x == StdlibSvcId::Memcpy as u32 => EmulatedFunction::call(&stdlib::memcpy, core, &mut ()).await?.write(core, lr),",
    "            x if x == StdlibSvcId::MemsetLegacy as u32 => EmulatedFunction::call(&stdlib::memset, core, &mut ()).await?.write(core, lr),",
    "            x if x == StdlibSvcId::Memset as u32 => EmulatedFunction::call(&stdlib::memset, core, &mut ()).await?.write(core, lr),",
])
if old not in text:
    raise SystemExit('Could not find stdlib dispatch insertion point for 0x415')
text = text.replace(old, new, 1)
stdlib.write_text(text, encoding='utf-8')

svc_check = svc.read_text(encoding='utf-8')
wipi_check = wipi.read_text(encoding='utf-8')
stdlib_check = stdlib.read_text(encoding='utf-8')
assert 'ListDatabases = 0x19c' in svc_check
assert '0x19c => Self::ListDatabases' in svc_check
assert 'MemsetLegacy = 0x415' in svc_check
assert 'WIPICSvcId::ListDatabases => database::list_databases.into_body()' in wipi_check
assert 'experimental LGT 0x12d fs-info shim' in wipi_check
assert 'StdlibSvcId::MemsetLegacy as u32' in stdlib_check
print('Zenonia v5 managed patch verification passed')
