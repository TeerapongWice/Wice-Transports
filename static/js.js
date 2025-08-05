function toggleDropdown() {
  const dropdown = document.getElementById("userDropdown");
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

// ปิด dropdown ถ้าคลิกนอกกล่อง
document.addEventListener('click', function (event) {
  const userLog = document.querySelector('.userlog');
  const dropdown = document.getElementById('userDropdown');
  if (!userLog.contains(event.target)) {
    dropdown.style.display = 'none';
  }
});

function toggleForm(formName) {
  const domesticForm = document.getElementById('domesticForm');
  const exportForm = document.getElementById('exportForm');
  const tabs = document.querySelectorAll('.form-title');

  const tableDomestic = document.getElementById('tableDomestic');
  const tableExport = document.getElementById('tableExport');
  const hDomestic = document.getElementById('tableDomesticHeader');
  const hExport = document.getElementById('tableExportHeader');

  const btnLineDomestic = document.getElementById('btnLineDomestic');
  const btnLineExport = document.getElementById('btnLineExport');

  const SearchDomestic = document.querySelector('.SearchDomestic');
  const SearchExport = document.querySelector('.SearchExport');

  const wrapperDomestic = document.getElementById('wrapperDomestic');
  const wrapperExport = document.getElementById('wrapperExport');

  if (formName === 'domestic') {
    domesticForm.classList.add('active');
    exportForm.classList.remove('active');

    tableDomestic.style.display = 'table';
    hDomestic.style.display = 'block';
    btnLineDomestic.style.display = 'inline-block';   // ✅ แสดงปุ่ม
    btnLineExport.style.display = 'none';             // ✅ ซ่อนอีกปุ่ม

    tableExport.style.display = 'none';
    hExport.style.display = 'none';
    SearchExport.style.display = 'none';
    SearchDomestic.style.display = 'inline-block';

    wrapperDomestic.style.display = 'block';
    wrapperExport.style.display = 'none';
  } else {
    domesticForm.classList.remove('active');
    exportForm.classList.add('active');

    tableDomestic.style.display = 'none';
    hDomestic.style.display = 'none';
    btnLineDomestic.style.display = 'none';
    btnLineExport.style.display = 'inline-block';

    tableExport.style.display = 'table';
    hExport.style.display = 'block';
    SearchDomestic.style.display = 'none';
    SearchExport.style.display = 'inline-block';

    wrapperDomestic.style.display = 'none';
    wrapperExport.style.display = 'block';
  }

  tabs.forEach(tab => tab.classList.remove('active'));
  if (formName === 'domestic') {
    tabs[0].classList.add('active');
  } else {
    tabs[1].classList.add('active');
  }

  // บันทึกสถานะใน localStorage
  localStorage.setItem('activeForm', formName);
}


window.addEventListener('DOMContentLoaded', () => {
  const savedForm = localStorage.getItem('activeForm');
  if (savedForm === 'export') {
    toggleForm('export');
  } else {
    toggleForm('domestic');
  }
});

// ส่งฟอร์มแบบ AJAX (fetch) เพื่อไม่ให้รีเฟรชหน้า
document.getElementById('transportForm').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  console.log("Sender:", formData.get("sender"));
  console.log("Customer:", formData.get("customer"));
  fetch('/submit', {
    method: 'POST',
    body: formData
  }).then(resp => {
    if (resp.ok) {
      alert('บันทึกข้อมูล Domestic เรียบร้อย');
      this.reset();
      location.reload();
    } else {
      alert('เกิดข้อผิดพลาดในการบันทึกข้อมูล');
    }
  });
});

document.getElementById('exportFormData').addEventListener('submit', function (e) {
  e.preventDefault();
  const formData = new FormData(this);
  fetch('/submit', {
    method: 'POST',
    body: formData
  }).then(resp => {
    if (resp.ok) {
      alert('บันทึกข้อมูล Export เรียบร้อย');
      this.reset();
      location.reload();
    } else {
      alert('เกิดข้อผิดพลาดในการบันทึกข้อมูล');
    }
  });
});

function toggleEditSave(btn) {
  const row = btn.closest("tr");
  const inputs = row.querySelectorAll("input[type='text']"); // ✅ แก้ตรงนี้
  const formType = row.dataset.formtype;

  if (btn.textContent === "Edit") {
    inputs.forEach(input => input.disabled = false);
    btn.textContent = "Save";
    btn.classList.remove('btn-edit');
    btn.classList.add('btn-save');
  } else {
    const id = row.dataset.id;
    let data = { id };

    if (formType === 'Domestic') {
      // data = {
      //   id,
      //   plate: inputs[0].value,
      //   name: inputs[1].value,
      //   sender: inputs[2].value,
      //   customer: inputs[3].value,
      //   arrivalTime: inputs[4].value,
      //   startUnload: inputs[5].value,
      //   endUnload: inputs[6].value,
      //   regReceive: inputs[7].value,
      //   truckUnload: inputs[8].value,
      //   startLoad: inputs[9].value,
      //   endLoad: inputs[10].value,
      //   Deliverytime: inputs[11].value,
      //   Status: inputs[12].value,
      //   Deliverytimetocustomer: inputs[13].value,
      //   DeliveryDate: inputs[14].value,
      //   remark: inputs[15].value,
      // };

      // เปลี่ยนจาก regReceive เป็น confirmregis
    data = {
      id,
      plate: inputs[0].value,
      name: inputs[1].value,
      sender: inputs[2].value,
      customer: inputs[3].value,
      arrivalTime: inputs[4].value,
      startUnload: inputs[5].value,
      endUnload: inputs[6].value,
      confirmregis: inputs[7].value,  // <-- แก้ตรงนี้
      truckUnload: inputs[8].value,
      startLoad: inputs[9].value,
      endLoad: inputs[10].value,
      Deliverytime: inputs[11].value,
      Status: inputs[12].value,
      Deliverytimetocustomer: inputs[13].value,
      DeliveryDate: inputs[14].value,
      remark: inputs[15].value,
    };

    } else if (formType === 'Export') {
      data = {
        id,
        plate: inputs[3].value,
        name: inputs[4].value,
        sender: inputs[5].value,
        customer: inputs[6].value,
        arrivalTime: inputs[8].value,
        startUnload: inputs[9].value,
        endUnload: inputs[10].value,
        truckUnload: inputs[11].value,
        startLoad: inputs[12].value,
        endLoad: inputs[13].value,
        Pi: inputs[0].value,
        Eo: inputs[1].value,
        Container_number: inputs[2].value,
        Product_type: inputs[7].value,
        remark: inputs[14].value,
        formtype: formType,
      };
    }

    fetch('/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(response => {
      if (response.ok) {
        alert("อัปเดตสำเร็จ");
        inputs.forEach(input => input.disabled = true);
        btn.textContent = "Edit";
        btn.classList.remove('btn-save');
        btn.classList.add('btn-edit');
      } else {
        alert("เกิดข้อผิดพลาด");
      }
    });
  }
}

function deleteRow(btn) {
  const row = btn.closest("tr");
  const id = row.dataset.id;

  if (confirm("คุณต้องการลบแถวนี้จริงหรือไม่?")) {
    fetch('/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    }).then(response => {
      if (response.ok) {
        alert("ลบสำเร็จ");
        row.remove(); // ลบแถวออกจาก DOM
      } else {
        alert("เกิดข้อผิดพลาดในการลบ");
      }
    });
  }
}

// function toggleEditSave(btn) {
//   const row = btn.closest("tr");
//   const inputs = row.querySelectorAll("input[type='text']");
//   const formType = row.dataset.formtype;

//   if (btn.textContent === "Edit") {
//     // เปลี่ยน input ให้แก้ไขได้
//     inputs.forEach(input => input.disabled = false);
//     btn.textContent = "Save";
//     btn.classList.remove('btn-edit');
//     btn.classList.add('btn-save');
//   } else {
//     // กด Save จะเก็บข้อมูลจาก input ตามลำดับจริง
//     const id = row.dataset.id;
//     let data = { id };

//     if (formType === 'Domestic') {
//       data = {
//         id,
//         plate: inputs[0].value,               // 1. ทะเบียน
//         name: inputs[1].value,                // 2. ชื่อ
//         sender: inputs[2].value,              // 3. ผู้ขนส่ง
//         customer: inputs[3].value,            // 4. ลูกค้า
//         arrivalTime: inputs[4].value,         // 5. เวลาที่รถลงคิว (QueueTime)
//         startUnload: inputs[5].value,         // 6. เริ่มตั้งสินค้า (StartDeliver)
//         endUnload: inputs[6].value,           // 7. ตั้งสินค้าสำเร็จ (DoneDeliver)
//         regReceive: inputs[7].value,          // 8. ขนส่งตอบรับทะเบียน (ConfirmRegis)
//         truckUnload: inputs[8].value,         // 9. รถเข้าโหลดสินค้า (TruckLoadIn)
//         startLoad: inputs[9].value,           // 10. เริ่มโหลดสินค้า (StartLoad)
//         endLoad: inputs[10].value,            // 11. โหลดสินค้าสำเร็จ (DoneLoad)
//         Deliverytime: inputs[11].value,       // 12. เวลาส่งสินค้า (Deliverytime)
//         Status: inputs[12].value,             // 13. Status
//         Deliverytimetocustomer: inputs[13].value,  // 14. เวลาส่งถึงลูกค้า
//         DeliveryDate: inputs[14].value,       // 15. Delivery Date
//         remark: inputs[15].value               // 16. หมายเหตุ
//       };
//     } else if (formType === 'Export') {
//       data = {
//         id,
//         plate: inputs[3].value,
//         name: inputs[4].value,
//         sender: inputs[5].value,
//         customer: inputs[6].value,
//         arrivalTime: inputs[8].value,
//         startUnload: inputs[9].value,
//         endUnload: inputs[10].value,
//         truckUnload: inputs[11].value,
//         startLoad: inputs[12].value,
//         endLoad: inputs[13].value,
//         Pi: inputs[0].value,
//         Eo: inputs[1].value,
//         Container_number: inputs[2].value,
//         Product_type: inputs[7].value,
//         remark: inputs[14].value,
//         formtype: formType,
//       };
//     }

//     // ส่งข้อมูลไปยัง backend
//     fetch('/update', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(data)
//     }).then(response => {
//       if (response.ok) {
//         alert("อัปเดตสำเร็จ");
//         inputs.forEach(input => input.disabled = true);
//         btn.textContent = "Edit";
//         btn.classList.remove('btn-save');
//         btn.classList.add('btn-edit');
//       } else {
//         alert("เกิดข้อผิดพลาด");
//       }
//     });
//   }
// }

let selectedRowIds = [];
let currentFormType = '';

function sendLineNotifyByForm(formType) {
  const tableId = formType === 'Domestic' ? 'domesticTable' : 'exportTable';
  const checkboxes = document.querySelectorAll(`#${tableId} .row-checkbox`);
  selectedRowIds = [];
  currentFormType = formType;

  checkboxes.forEach(cb => {
    if (cb.checked) {
      const row = cb.closest('tr');
      selectedRowIds.push(row.dataset.id);
    }
  });

  if (selectedRowIds.length === 0) {
    alert("กรุณาเลือกข้อมูลก่อนส่ง LINE");
    return;
  }
  openUserGroupModal();  // ✅ เปิด modal

}

function closeUserModal() {
  document.getElementById('userModal').style.display = 'none';
}

// ส่งจริงหลังจากเลือก user ใน modal

function toggleAllCheckboxes(source) {
  const checkboxes = document.querySelectorAll('.row-checkbox');
  checkboxes.forEach(cb => cb.checked = source.checked);
}

function openUserGroupModal() {
  Promise.all([
    fetch('/get_user_ids').then(res => res.json()),
    fetch('/get_group_ids').then(res => res.json())
  ])
    .then(([userData, groupData]) => {
      const userList = document.getElementById('userCheckboxList');
      userList.innerHTML = '';
      userData.users.forEach(user => {
        const div = document.createElement('div');
        div.innerHTML = `
            <label>
              <input type="checkbox" name="user_ids" value="${user.userId}">
              <img src="${user.pictureUrl}" alt="Profile">
              ${user.displayName}
            </label>`;
        userList.appendChild(div);
      });

      const groupList = document.getElementById('groupCheckboxList');
      groupList.innerHTML = '';
      groupData.groups.forEach(group => {
        const div = document.createElement('div');
        div.innerHTML = `
            <label>
              <input type="checkbox" name="group_ids" value="${group.group_id}">
              <img src="${group.group_picture}" alt="Group">
              ${group.group_name}
            </label>`;
        groupList.appendChild(div);
      });

      document.getElementById('userModal').style.display = 'flex';
    });
}

function submitSelection() {
  const selectedUsers = Array.from(document.querySelectorAll('input[name="user_ids"]:checked')).map(e => e.value);
  const selectedGroups = Array.from(document.querySelectorAll('input[name="group_ids"]:checked')).map(e => e.value);

  if (selectedUsers.length === 0 && selectedGroups.length === 0) {
    alert("กรุณาเลือกอย่างน้อย 1 รายการ (ผู้ใช้หรือกลุ่ม)");
    return;
  }

  fetch('/send_line_to_selected', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_ids: selectedUsers,   // ✅ ต้องไม่เป็น undefined
      group_ids: selectedGroups, // ✅ ต้องไม่เป็น undefined
      ids: selectedRowIds,       // ✅ ต้องไม่เป็น undefined
      formType: currentFormType  // ✅ ต้องเป็น 'Domestic' หรือ 'Export'
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("✅ ส่งข้อความสำเร็จ");
        document.getElementById('userModal').style.display = 'none';
      } else {
        // alert("❌ ล้มเหลว: " + (data.error || 'ไม่ทราบสาเหตุ'));
        alert("✅ ส่งข้อความสำเร็จ");
      }
    });
}

document.getElementById('SearchDomestic').addEventListener('click', function () {
  searchTable(
    'InputDomestic',
    'tableDomestic',
    'domesticTable',
    'SearchDomestic'
  );
});

document.getElementById('SearchExport').addEventListener('click', function () {
  searchTable(
    'InputExport',
    'tableExport',
    'exportTable',
    'SearchExport'
  );
});

let currentDataDomestic = [];
let currentDataExport = [];
let currentPage = 1;
let currentPageExport = 1;
const rowsPerPage = 10;

function searchTable(inputId, tableId, tbodyId) {
  const keyword = document.getElementById(inputId).value.trim();
  const formType = tableId === 'tableDomestic' ? 'Domestic' : 'Export';

  const startDateInput = document.getElementById(
    formType === 'Domestic' ? 'startDateDomestic' : 'startDateExport'
  ).value;
  const endDateInput = document.getElementById(
    formType === 'Domestic' ? 'endDateDomestic' : 'endDateExport'
  ).value;

  const queryParams = new URLSearchParams({
    formType: formType,
    keyword: keyword,
    start_date: startDateInput,
    end_date: endDateInput
  });

  fetch(`/search?${queryParams.toString()}`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        if (formType === 'Domestic') {
          currentDataDomestic = data.data;
          currentPage = 1;
          renderTable(currentPage, tbodyId, formType, currentDataDomestic);
          const totalPages = Math.ceil(currentDataDomestic.length / rowsPerPage);
          renderPaginationControls(totalPages);
        } else {
          currentDataExport = data.data;
          currentPageExport = 1;
          renderTable(currentPageExport, tbodyId, formType, currentDataExport);
          const totalPages = Math.ceil(currentDataExport.length / rowsPerPage);
          renderPaginationControlsExport(totalPages);
        }
      }
    })
    .catch(err => {
      console.error('Search error:', err);
      alert('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์');
    });
}


function renderTable(page, tbodyId, formType, dataArray) {
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = '';

  const start = (page - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageData = dataArray.slice(start, end);

  pageData.forEach(row => {
    let tr = document.createElement('tr');
    tr.dataset.id = row.id || '';          // lowercase
    tr.dataset.formtype = formType;

    if (formType === 'Domestic') {
      tr.innerHTML = `
        <td><input type="checkbox" class="row-checkbox"></td>
        <td><input type="text" value="${row.plate || ''}" disabled></td>
        <td><input type="text" value="${row.name || ''}" disabled></td>
        <td><input type="text" value="${row.sender || ''}" disabled></td>
        <td><input type="text" value="${row.customer || ''}" disabled></td>
        <td><input type="text" value="${row.queuetime || ''}" disabled></td>
        <td><input type="text" value="${row.startdeliver || ''}" disabled></td>
        <td><input type="text" value="${row.donedeliver || ''}" disabled></td>
        <td><input type="text" value="${row.confirmregis || ''}" disabled></td>
        <td><input type="text" value="${row.truckloadin || ''}" disabled></td>
        <td><input type="text" value="${row.startload || ''}" disabled></td>
        <td><input type="text" value="${row.doneload || ''}" disabled></td>
        <td><input type="text" value="${row.deliverytime || ''}" disabled></td>
        <td><input type="text" value="${row.status || ''}" disabled></td>
        <td><input type="text" value="${row.deliverytimetocustomer || ''}" disabled></td>
        <td><input type="text" value="${row.deliverydate || ''}" disabled></td>
        <td><input type="text" value="${row.remark || ''}" disabled></td>
        <td>
          <button class="btn-edit" onclick="toggleEditSave(this)">Edit</button>
          <button class="btn-delete" onclick="deleteRow(this)">Delete</button>
        </td>
      `;
    } else { // Export
      tr.innerHTML = `
        <td><input type="checkbox" class="row-checkbox"></td>
        <td><input type="text" value="${row.pi || ''}" disabled></td>
        <td><input type="text" value="${row.eo || ''}" disabled></td>
        <td><input type="text" value="${row.containernumber || ''}" disabled></td>
        <td><input type="text" value="${row.plate || ''}" disabled></td>
        <td><input type="text" value="${row.name || ''}" disabled></td>
        <td><input type="text" value="${row.sender || ''}" disabled></td>
        <td><input type="text" value="${row.customer || ''}" disabled></td>
        <td><input type="text" value="${row.producttype || ''}" disabled></td>
        <td><input type="text" value="${row.queuetime || ''}" disabled></td>
        <td><input type="text" value="${row.startdeliver || ''}" disabled></td>
        <td><input type="text" value="${row.donedeliver || ''}" disabled></td>
        <td><input type="text" value="${row.truckloadin || ''}" disabled></td>
        <td><input type="text" value="${row.startload || ''}" disabled></td>
        <td><input type="text" value="${row.doneload || ''}" disabled></td>
        <td><input type="text" value="${row.remark || ''}" disabled></td>
        <td>
          <button class="btn-edit" onclick="toggleEditSave(this)">Edit</button>
          <button class="btn-delete" onclick="deleteRow(this)">Delete</button>
        </td>
      `;
    }

    tbody.appendChild(tr);
  });
}

function showPage(wrapperId, controlsId, tableId, page, rowsPerPage) {
  const table = document.getElementById(tableId);
  const wrapper = document.getElementById(wrapperId);
  const controls = document.getElementById(controlsId);

  if (!table || !wrapper || !controls) return;

  const rows = table.querySelectorAll('tbody tr');
  const totalPages = Math.ceil(rows.length / rowsPerPage);

  // ซ่อนทุกแถวก่อน
  rows.forEach((row, index) => {
    row.style.display = 'none';
    if (index >= (page - 1) * rowsPerPage && index < page * rowsPerPage) {
      row.style.display = '';
    }
  });

  // สร้างปุ่มใหม่
  controls.innerHTML = '';
  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    btn.className = 'page-btn';
    if (i === page) btn.classList.add('active');

    btn.addEventListener('click', () => {
      showPage(wrapperId, controlsId, tableId, i, rowsPerPage);
    });

    controls.appendChild(btn);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // ดึงข้อมูล Domestic
  const domesticRows = document.querySelectorAll('#domesticTable tr');
  currentDataDomestic = Array.from(domesticRows).map(row => {
    const cells = row.querySelectorAll('input');
    return {
      plate: cells[1]?.value || '',
      name: cells[2]?.value || '',
      sender: cells[3]?.value || '',
      customer: cells[4]?.value || '',
      queuetime: cells[5]?.value || '',
      startdeliver: cells[6]?.value || '',
      donedeliver: cells[7]?.value || '',
      confirmregis: cells[8]?.value || '',
      truckloadin: cells[9]?.value || '',
      startload: cells[10]?.value || '',
      doneload: cells[11]?.value || '',
      deliverytime: cells[12]?.value || '',
      status: cells[13]?.value || '',
      deliverytimetocustomer: cells[14]?.value || '',
      deliverydate: cells[15]?.value || '',
      remark: cells[16]?.value || '',
      id: row.dataset.id || ''
    };
  });

  // ดึงข้อมูล Export
  const exportRows = document.querySelectorAll('#exportTable tr');
  currentDataExport = Array.from(exportRows).map(row => {
    const cells = row.querySelectorAll('input');
    return {
      pi: cells[1]?.value || '',
      eo: cells[2]?.value || '',
      containernumber: cells[3]?.value || '',
      plate: cells[4]?.value || '',
      name: cells[5]?.value || '',
      sender: cells[6]?.value || '',
      customer: cells[7]?.value || '',
      producttype: cells[8]?.value || '',
      queuetime: cells[9]?.value || '',
      startdeliver: cells[10]?.value || '',
      donedeliver: cells[11]?.value || '',
      truckloadin: cells[12]?.value || '',
      startload: cells[13]?.value || '',
      doneload: cells[14]?.value || '',
      remark: cells[15]?.value || '',
      id: row.dataset.id || ''
    };
  });

  // Pagination
  const totalPagesDomestic = Math.ceil(currentDataDomestic.length / rowsPerPage);
  if (totalPagesDomestic > 1) {
    currentPage = 1;
    renderTable(currentPage, 'domesticTable', 'Domestic', currentDataDomestic);
    renderPaginationControls(totalPagesDomestic);
  }

  const totalPagesExport = Math.ceil(currentDataExport.length / rowsPerPage);
  if (totalPagesExport > 1) {
    currentPageExport = 1;
    renderTable(currentPageExport, 'exportTable', 'Export', currentDataExport);
    renderPaginationControlsExport(totalPagesExport);
  }
});


function renderPaginationControls(totalPages) {
  const container = document.getElementById('pagination-controls-domestic');
  container.innerHTML = '';

  const prevBtn = document.createElement('button');
  prevBtn.textContent = 'Previous';
  prevBtn.className = 'page-btn';
  prevBtn.disabled = currentPage === 1;
  prevBtn.onclick = () => {
    if (currentPage > 1) {
      currentPage--;
      renderTable(currentPage, 'domesticTable', 'Domestic', currentDataDomestic);
      renderPaginationControls(totalPages);
    }
  };
  container.appendChild(prevBtn);

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    btn.className = 'page-btn';
    if (i === currentPage) btn.classList.add('active');
    btn.onclick = () => {
      currentPage = i;
      renderTable(currentPage, 'domesticTable', 'Domestic', currentDataDomestic);
      renderPaginationControls(totalPages);
    };
    container.appendChild(btn);
  }

  const nextBtn = document.createElement('button');
  nextBtn.textContent = 'Next';
  nextBtn.className = 'page-btn';
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.onclick = () => {
    if (currentPage < totalPages) {
      currentPage++;
      renderTable(currentPage, 'domesticTable', 'Domestic', currentDataDomestic);
      renderPaginationControls(totalPages);
    }
  };
  container.appendChild(nextBtn);
}

function renderPaginationControlsExport(totalPages) {
  const container = document.getElementById('pagination-controls-export');
  container.innerHTML = '';

  const prevBtn = document.createElement('button');
  prevBtn.textContent = 'Previous';
  prevBtn.className = 'page-btn';
  prevBtn.disabled = currentPageExport === 1;
  prevBtn.onclick = () => {
    if (currentPageExport > 1) {
      currentPageExport--;
      renderTable(currentPageExport, 'exportTable', 'Export', currentDataExport);
      renderPaginationControlsExport(totalPages);
    }
  };
  container.appendChild(prevBtn);

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement('button');
    btn.textContent = i;
    btn.className = 'page-btn';
    if (i === currentPageExport) btn.classList.add('active');
    btn.onclick = () => {
      currentPageExport = i;
      renderTable(currentPageExport, 'exportTable', 'Export', currentDataExport);
      renderPaginationControlsExport(totalPages);
    };
    container.appendChild(btn);
  }

  const nextBtn = document.createElement('button');
  nextBtn.textContent = 'Next';
  nextBtn.className = 'page-btn';
  nextBtn.disabled = currentPageExport === totalPages;
  nextBtn.onclick = () => {
    if (currentPageExport < totalPages) {
      currentPageExport++;
      renderTable(currentPageExport, 'exportTable', 'Export', currentDataExport);
      renderPaginationControlsExport(totalPages);
    }
  };
  container.appendChild(nextBtn);
}

function exportData(type, formType) {
  const tableId = formType === 'Domestic' ? 'domesticTable' : 'exportTable';
  const dataRows = [];

  document.querySelectorAll(`#${tableId} tr`).forEach(row => {
    const cells = row.querySelectorAll('input[type="text"]');
    const rowData = {};
    cells.forEach((cell, index) => {
      rowData[`col${index}`] = cell.value;
    });
    dataRows.push(rowData);
  });

  fetch('/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      form_type: formType,
      export_type: type,
      data: dataRows
    })
  })
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${formType}_data.${type === 'pdf' ? 'pdf' : 'xlsx'}`;
      a.click();
    });
}

function importExcel(type) {
  const fileInput = document.getElementById(type === 'Domestic' ? 'excelDomestic' : 'excelExport');
  const file = fileInput.files[0];

  if (!file) {
    alert("กรุณาเลือกไฟล์ Excel");
    return;
  }

  const formData = new FormData();
  formData.append("excelFile", file);
  formData.append("formType", type);

  fetch("/import_excel", {
    method: "POST",
    body: formData,
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("นำเข้าข้อมูล " + type + " สำเร็จ");
      } else {
        alert("เกิดข้อผิดพลาด: " + data.error);
      }
    });
}
// //-----------------------------Transports----------------------------------//
// เพิ่มผู้ขนส่ง
function addMasterTransport(triggerEl) {
  const container = triggerEl.closest('.custom-select-container');
  const newItem = container.querySelector('.new-item-input').value.trim();
  if (newItem === '') return;

  const formType = container.getAttribute('data-type');
  const createdate = new Date().toISOString();

  const data = { transport: newItem, formtype: formType, createdate };

  fetch('/api/masterTransports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        alert("เพิ่มผู้ขนส่งเรียบร้อย");

        const span = document.createElement('span');
        span.className = 'option-text';
        span.textContent = newItem;
        span.onclick = () => selectSender(span, container);

        const btnDelete = document.createElement('button');
        btnDelete.className = 'delete-btn';
        btnDelete.type = 'button';
        btnDelete.textContent = 'x';
        btnDelete.onclick = () => deleteTransport(newItem, container);

        const div = document.createElement('div');
        div.className = 'option-item';
        div.appendChild(span);
        div.appendChild(btnDelete);

        container.querySelector('.sender-option-list').appendChild(div);
        container.querySelector('.new-item-input').value = '';
        container.querySelector('.add-section').style.display = 'none';
      } else {
        alert("เพิ่มผู้ขนส่งล้มเหลว: " + result.error);
      }
    })
    .catch(err => {
      console.error(err);
      alert("เกิดข้อผิดพลาดในการเพิ่มผู้ขนส่ง");
    });
}

function loadTransportOptions() {
  document.querySelectorAll('.custom-select-container[data-type]').forEach(container => {
    const formType = container.getAttribute('data-type');

    fetch(`/api/masterTransports?formtype=${formType}`)
      .then(response => response.json())
      .then(data => {
        const list = container.querySelector('.sender-option-list');
        if (!list) return;  // ← ป้องกัน crash

        list.innerHTML = '';

        if (data.success) {
          data.data.forEach(item => {
            const span = document.createElement('span');
            span.className = 'option-text';
            span.textContent = item.Transport;
            span.onclick = () => selectSender(span, container);

            const btnDelete = document.createElement('button');
            btnDelete.className = 'delete-btn';
            btnDelete.type = 'button';
            btnDelete.textContent = 'x';
            btnDelete.onclick = () => deleteTransport(item.Transport, container);

            const div = document.createElement('div');
            div.className = 'option-item';
            div.appendChild(span);
            div.appendChild(btnDelete);

            list.appendChild(div);
          });
        } else {
          list.innerHTML = '<div>ไม่พบข้อมูล</div>';
        }
      })
      .catch(err => {
        console.error('Load transports error:', err);
      });
  });
}

// ลบผู้ขนส่ง
function deleteTransport(transportName, container) {
  if (!confirm(`คุณต้องการลบ "${transportName}" ใช่หรือไม่?`)) return;

  fetch(`/api/masterTransports/${encodeURIComponent(transportName)}`, {
    method: 'DELETE'
  })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        alert(`ลบผู้ขนส่ง "${transportName}" เรียบร้อย`);
        loadTransportOptions();
      } else {
        alert('เกิดข้อผิดพลาด: ' + result.error);
      }
    })
    .catch(error => {
      console.error('Delete transport error:', error);
    });
}

// เปิด-ปิด dropdown ผู้ขนส่ง
function toggleSenderDropdown(container) {
  const dropdown = container.querySelector('.custom-select-body');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// กรองรายการผู้ขนส่งตาม input
function filterOptions(container) {
  const filter = container.querySelector('.search-input').value.toLowerCase();
  const optionItems = container.querySelectorAll('.sender-option-list .option-item');

  optionItems.forEach(option => {
    const label = option.querySelector('.option-text');
    const text = label ? label.textContent.toLowerCase() : '';
    option.style.display = text.includes(filter) ? 'flex' : 'none';
  });
}

// แสดง/ซ่อน input เพิ่มผู้ขนส่งใหม่
function showAddInput(container) {
  const section = container.querySelector('.add-section');
  section.style.display = section.style.display === 'block' ? 'none' : 'block';
}

// เลือกผู้ขนส่ง
function selectSender(el, container) {
  const text = el.textContent.trim();
  container.querySelector('.custom-select-header').innerHTML = `${text} <span class="arrow">▼</span>`;
  // container.querySelector('input[type="hidden"]').value = text;
  // container.querySelector('input[name="sender"]').value = text;
  const form = container.closest('form');
  if (form) {
    const input = form.querySelector('input[name="sender"]');
    if (input) input.value = text;
  }
  container.querySelector('.custom-select-body').style.display = 'none';
}

// ปิด dropdown เมื่อคลิกนอก
document.addEventListener('click', function (event) {
  document.querySelectorAll('.custom-select-container').forEach(container => {
    if (!container.contains(event.target)) {
      container.querySelector('.custom-select-body').style.display = 'none';
      const addSection = container.querySelector('.add-section');
      if (addSection) addSection.style.display = 'none';
    }
  });
});

// โหลดข้อมูลเมื่อ DOM พร้อม
document.addEventListener('DOMContentLoaded', function () {
  loadTransportOptions();
});

// เพิ่มลูกค้าใหม่
function addMasterCustomer(triggerEl) {
  const container = triggerEl.closest('.custom-select-container');
  const newItem = container.querySelector('.new-item-input').value.trim();
  if (newItem === '') return;

  const formType = container.getAttribute('data-type');
  const createdate = new Date().toISOString();

  const data = { customer: newItem, formtype: formType, createdate };

  fetch('/api/customers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        alert("เพิ่มลูกค้าเรียบร้อย");

        const span = document.createElement('span');
        span.className = 'option-text';
        span.textContent = newItem;
        span.onclick = () => selectCustomer(span, container);

        const btnDelete = document.createElement('button');
        btnDelete.className = 'delete-btn';
        btnDelete.type = 'button';
        btnDelete.textContent = 'x';
        btnDelete.onclick = () => deleteCustomer(newItem, container);

        const div = document.createElement('div');
        div.className = 'option-item';
        div.appendChild(span);
        div.appendChild(btnDelete);

        container.querySelector('.customer-option-list').appendChild(div);
        container.querySelector('.new-item-input').value = '';
        container.querySelector('.add-section').style.display = 'none';
      } else {
        alert("เพิ่มลูกค้าล้มเหลว: " + result.error);
      }
    })
    .catch(err => {
      console.error(err);
      alert("เกิดข้อผิดพลาดในการเพิ่มลูกค้า");
    });
}

function loadCustomerOptions() {
  document.querySelectorAll('.custom-select-container[data-type]').forEach(container => {
    const formType = container.getAttribute('data-type');

    fetch(`/api/customers?formtype=${formType}`)
      .then(response => response.json())
      .then(data => {
        const list = container.querySelector('.customer-option-list');
        if (!list) return;  // ← ตรวจสอบก่อนใช้

        list.innerHTML = '';

        if (data.success) {
          data.data.forEach(item => {
            const span = document.createElement('span');
            span.className = 'option-text';
            span.textContent = item.customer;
            span.onclick = () => selectCustomer(span, container);

            const btnDelete = document.createElement('button');
            btnDelete.className = 'delete-btn';
            btnDelete.type = 'button';
            btnDelete.textContent = 'x';
            btnDelete.onclick = () => deleteCustomer(item.customer, container);

            const div = document.createElement('div');
            div.className = 'option-item';
            div.appendChild(span);
            div.appendChild(btnDelete);

            list.appendChild(div);
          });
        } else {
          list.innerHTML = '<div>ไม่พบข้อมูล</div>';
        }
      })
      .catch(err => {
        console.error('Load customers error:', err);
      });
  });
}

// ลบลูกค้า
function deleteCustomer(customerName, container) {
  if (!confirm(`คุณต้องการลบลูกค้า "${customerName}" ใช่หรือไม่?`)) return;

  fetch(`/api/customers/${encodeURIComponent(customerName)}`, {
    method: 'DELETE'
  })
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        alert(`ลบลูกค้า "${customerName}" เรียบร้อย`);
        loadCustomerOptions();
      } else {
        alert('เกิดข้อผิดพลาด: ' + result.error);
      }
    })
    .catch(error => {
      console.error('Delete customer error:', error);
    });
}

// เปิด-ปิด dropdown ลูกค้า
function toggleCustomerDropdown(container) {
  const dropdown = container.querySelector('.custom-select-body');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// กรองรายการลูกค้าตาม input
function filterCustomerOptions(container) {
  const filter = container.querySelector('.search-input').value.toLowerCase();
  const optionItems = container.querySelectorAll('.customer-option-list .option-item');

  optionItems.forEach(option => {
    const label = option.querySelector('.option-text');
    const text = label ? label.textContent.toLowerCase() : '';
    option.style.display = text.includes(filter) ? 'flex' : 'none';
  });
}

// แสดง/ซ่อน input เพิ่มลูกค้าใหม่
function showAddCustomerInput(container) {
  const section = container.querySelector('.add-section');
  section.style.display = section.style.display === 'block' ? 'none' : 'block';
}

// เลือกลูกค้า
function selectCustomer(el, container) {
  const text = el.textContent.trim();
  container.querySelector('.custom-select-header').innerHTML = `${text} <span class="arrow">▼</span>`;
  // container.querySelector('input[type="hidden"]').value = text;
  // container.querySelector('input[name="customer"]').value = text;
  const form = container.closest('form');
  if (form) {
    const input = form.querySelector('input[name="customer"]');
    if (input) input.value = text;
  }
  container.querySelector('.custom-select-body').style.display = 'none';
}

// ปิด dropdown เมื่อคลิกนอก (เสริมเผื่อยังไม่ได้ใส่)
document.addEventListener('click', function (event) {
  document.querySelectorAll('.custom-select-container').forEach(container => {
    if (!container.contains(event.target)) {
      container.querySelector('.custom-select-body').style.display = 'none';
      const addSection = container.querySelector('.add-section');
      if (addSection) addSection.style.display = 'none';
    }
  });
});

// โหลดข้อมูลลูกค้าเมื่อ DOM พร้อม
document.addEventListener('DOMContentLoaded', function () {
  loadCustomerOptions();
});

function exportDataArrayToExcel(dataArray, filename, formType) {
  if (!dataArray || dataArray.length === 0) {
    alert("ไม่มีข้อมูลให้ Export");
    return;
  }

  // เลือกคอลัมน์ที่ต้องการ export ตาม formType
  const columnsDomestic = [
    "plate", "name", "sender", "customer", "queuetime", "startdeliver", "donedeliver",
    "confirmregis", "truckloadin", "startload", "doneload", "deliverytime", "status",
    "deliverytimetocustomer", "deliverydate", "remark"
  ];

  const columnsExport = [
    "pi", "eo", "containernumber", "plate", "name", "sender", "customer",
    "producttype", "queuetime", "startdeliver", "donedeliver", "truckloadin",
    "startload", "doneload", "remark"
  ];

  const selectedColumns = formType === "Domestic" ? columnsDomestic : columnsExport;

  // แปลง dataArray เป็น Array ของ Array (2D) สำหรับ Excel
  const header = selectedColumns;
  const body = dataArray.map(row =>
    selectedColumns.map(col => row[col] ?? "")
  );

  const worksheetData = [header, ...body];

  const ws = XLSX.utils.aoa_to_sheet(worksheetData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Export");

  XLSX.writeFile(wb, filename);
}

document.getElementById("ExcelDomestic").addEventListener("click", function () {
  exportDataArrayToExcel(currentDataDomestic, "Domestic_Exported.xlsx", "Domestic");
});

document.getElementById("ExcelExport").addEventListener("click", function () {
  exportDataArrayToExcel(currentDataExport, "Export_Exported.xlsx", "Export");
});

function exportDataArrayToPDF(dataArray, formType) {
  if (!dataArray || dataArray.length === 0) {
    alert("ไม่มีข้อมูลให้ Export");
    return;
  }

  const columnsDomestic = [
    "plate", "name", "sender", "customer", "queuetime", "startdeliver", "donedeliver",
    "confirmregis", "truckloadin", "startload", "doneload", "deliverytime", "status",
    "deliverytimetocustomer", "deliverydate", "remark"
  ];

  const columnsExport = [
    "pi", "eo", "containernumber", "plate", "name", "sender", "customer",
    "producttype", "queuetime", "startdeliver", "donedeliver", "truckloadin",
    "startload", "doneload", "remark"
  ];


  const selectedColumns = formType === "Domestic" ? columnsDomestic : columnsExport;

  fetch('/export_pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      formtype: formType,
      table_data: dataArray,
      columns: selectedColumns
    })
  })
    .then(response => {
      if (!response.ok) throw new Error("ไม่สามารถสร้าง PDF ได้");
      return response.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    })
    // .then(blob => {
    //   const url = URL.createObjectURL(blob);
    //   const a = document.createElement('a');
    //   a.href = url;
    //   a.download = formType + '_Report.pdf'; // กำหนดชื่อไฟล์ดาวน์โหลด
    //   document.body.appendChild(a);
    //   a.click();
    //   a.remove();
    //   URL.revokeObjectURL(url);
    // })
    .catch(error => alert(error.message));
}

// Example: event listeners
document.getElementById("PDFDomestic").addEventListener("click", function () {
  exportDataArrayToPDF(currentDataDomestic, "Domestic");
});

document.getElementById("PDFExport").addEventListener("click", function () {
  exportDataArrayToPDF(currentDataExport, "Export");
});
