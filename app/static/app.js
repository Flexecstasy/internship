const vacancyCards = document.getElementById('vacancyCards');
const vacancyDetailsView = document.getElementById('vacancyDetailsView');
const vacancyListView = document.getElementById('vacancyListView');
const applicationsView = document.getElementById('applicationsView');
const alertBox = document.getElementById('alertBox');
const applicationsList = document.getElementById('applicationsList');

function showAlert(type, message) {
  alertBox.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function clearAlert() {
  alertBox.innerHTML = '';
}

function showView(name) {
  vacancyListView.classList.toggle('d-none', name !== 'list');
  vacancyDetailsView.classList.toggle('d-none', name !== 'details');
  applicationsView.classList.toggle('d-none', name !== 'applications');
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw data;
  }
  return data;
}

async function loadVacancies() {
  clearAlert();
  const vacancies = await apiFetch('/api/vacancies');
  vacancyCards.innerHTML = vacancies
    .map(
      (vacancy) => `
      <div class="col-12 col-md-6">
        <article class="card vacancy-card h-100">
          <div class="card-body d-flex flex-column">
            <h3 class="h5">${vacancy.title}</h3>
            <p class="text-muted mb-2">${vacancy.department}</p>
            <p class="salary-chip mb-3">${vacancy.salary_per_hour} ₽/час · ${vacancy.workload_hours} ч/нед</p>
            <button class="btn btn-primary mt-auto" onclick="openVacancy(${vacancy.id})">Открыть карточку</button>
          </div>
        </article>
      </div>`
    )
    .join('');
}

async function openVacancy(vacancyId) {
  clearAlert();
  try {
    const vacancy = await apiFetch(`/api/vacancies/${vacancyId}`);
    vacancyDetailsView.innerHTML = `
      <div class="card vacancy-card">
        <div class="card-body">
          <button class="btn btn-link px-0 mb-2" onclick="showView('list')">← Назад к списку</button>
          <h2 class="h4">${vacancy.title}</h2>
          <p class="text-muted">${vacancy.department} · ${vacancy.location}</p>
          <p>${vacancy.description}</p>
          <p><strong>Работодатель:</strong> ${vacancy.employer}</p>
          <p><strong>Оплата:</strong> ${vacancy.salary_per_hour} ₽/час</p>
          <form id="applyForm" class="row g-2 mt-2">
            <div class="col-12 col-md-6"><input class="form-control" name="student_full_name" placeholder="ФИО" required /></div>
            <div class="col-12 col-md-6"><input class="form-control" type="email" name="student_email" placeholder="Email" required /></div>
            <div class="col-12 col-md-6"><input class="form-control" name="faculty" placeholder="Факультет" required /></div>
            <div class="col-12 col-md-6"><input class="form-control" type="number" name="study_year" min="1" max="6" placeholder="Курс" required /></div>
            <div class="col-12"><textarea class="form-control" name="cover_letter" rows="4" placeholder="Короткое сопроводительное письмо (минимум 30 символов)" required></textarea></div>
            <div class="col-12 col-md-4"><button class="btn btn-success w-100" type="submit">Откликнуться</button></div>
          </form>
        </div>
      </div>`;

    document.getElementById('applyForm').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.target;
      const payload = Object.fromEntries(new FormData(form).entries());
      payload.study_year = Number(payload.study_year);
      try {
        const result = await apiFetch(`/api/vacancies/${vacancyId}/apply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        showAlert('success', `Отклик #${result.id} успешно отправлен.`);
        document.getElementById('filterEmail').value = payload.student_email;
      } catch (error) {
        showAlert('danger', `${error.user_message}<br><small>${error.suggestion}</small>`);
      }
    });

    showView('details');
  } catch (error) {
    showAlert('danger', `${error.user_message}<br><small>${error.suggestion}</small>`);
  }
}

async function loadApplications(email) {
  clearAlert();
  try {
    const apps = await apiFetch(`/api/applications?student_email=${encodeURIComponent(email)}`);
    applicationsList.innerHTML = apps.length
      ? apps
          .map(
            (app) => `<div class="list-group-item"><strong>${app.vacancy_title}</strong><br><span class="text-muted">Статус: ${app.status}</span></div>`
          )
          .join('')
      : '<div class="list-group-item">Откликов пока нет.</div>';
  } catch (error) {
    showAlert('danger', `${error.user_message}<br><small>${error.suggestion}</small>`);
    applicationsList.innerHTML = '';
  }
}

document.getElementById('goApplications').addEventListener('click', () => showView('applications'));
document.getElementById('goHome').addEventListener('click', () => showView('list'));
document.getElementById('applicationsFilterForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  await loadApplications(document.getElementById('filterEmail').value);
});

loadVacancies().catch(() => showAlert('danger', 'Не удалось загрузить вакансии.'));
window.openVacancy = openVacancy;
window.showView = showView;
