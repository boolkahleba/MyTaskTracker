import csv
import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from boards.models import Board, BoardStatus, BoardMember
from tasks.models import Task
from predictions.models import HistoricalTaskData
from predictions.predictors import retrain_model_if_possible, create_or_update_prediction


class Command(BaseCommand):
    help = 'Импорт задач из processed_tasks_full.csv для обучения и тестирования модели'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='processed_tasks_full.csv',
            help='Путь к CSV-файлу'
        )
        parser.add_argument(
            '--random-state',
            type=int,
            default=42,
            help='Фиксированное зерно для разделения train/test'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        random_state = options['random_state']

        with transaction.atomic():
            managers = self.create_managers()
            users = self.create_users()
            board, statuses = self.create_board(managers[0], managers, users)

            rows_by_issue = self.read_unique_tasks(file_path)
            issue_ids = list(rows_by_issue.keys())

            if not issue_ids:
                self.stdout.write(self.style.ERROR('Файл пустой или не содержит задач'))
                return

            rnd = random.Random(random_state)
            test_count = min(80, len(issue_ids))
            test_issue_ids = set(rnd.sample(issue_ids, test_count))

            train_rows = []
            test_rows = []

            for issue_id, row in rows_by_issue.items():
                if issue_id in test_issue_ids:
                    test_rows.append(row)
                else:
                    train_rows.append(row)

            self.stdout.write(f'Обучающих задач: {len(train_rows)}')
            self.stdout.write(f'Тестовых задач: {len(test_rows)}')

            created_train = self.create_train_tasks(
                train_rows=train_rows,
                board=board,
                done_status=statuses['done'],
                managers=managers,
                users=users
            )

            model_trained = retrain_model_if_possible()
            if model_trained:
                self.stdout.write(self.style.SUCCESS('Модель успешно обучена'))
            else:
                self.stdout.write(self.style.WARNING('Недостаточно данных для обучения модели'))

            created_test = self.create_test_tasks(
                test_rows=test_rows,
                board=board,
                open_status=statuses['open'],
                managers=managers,
                users=users
            )

            for task in created_test:
                create_or_update_prediction(task)

            self.stdout.write(self.style.SUCCESS('Импорт завершён'))
            self.stdout.write(f'Создано обучающих задач: {len(created_train)}')
            self.stdout.write(f'Создано тестовых задач: {len(created_test)}')

    def create_managers(self):
        manager_names = [
            'Алексей Смирнов',
            'Мария Иванова',
            'Дмитрий Кузнецов',
            'Екатерина Соколова',
        ]

        managers = []

        for index, full_name in enumerate(manager_names, start=1):
            email = f'manager{index}@example.com'

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'is_staff': True,
                    'is_admin': True,
                }
            )

            user.full_name = full_name
            user.is_staff = True
            user.is_admin = True
            user.set_password('admin')
            user.save()

            managers.append(user)

        return managers

    def create_users(self):
        user_names = [
            'Иван Петров',
            'Анна Васильева',
            'Сергей Николаев',
            'Ольга Фёдорова',
            'Павел Морозов',
            'Наталья Волкова',
            'Артём Попов',
            'Татьяна Лебедева',
            'Максим Семёнов',
            'Елена Козлова',
            'Никита Новиков',
            'Юлия Андреева',
            'Кирилл Макаров',
            'Алина Захарова',
            'Роман Павлов',
            'Виктория Орлова',
            'Глеб Сидоров',
            'Светлана Белова',
        ]

        users = []

        for index, full_name in enumerate(user_names, start=1):
            email = f'user{index}@example.com'

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'is_staff': False,
                    'is_admin': False,
                }
            )

            user.full_name = full_name
            user.is_staff = False
            user.is_admin = False
            user.set_password('admin123')
            user.save()

            users.append(user)

        return users

    def create_board(self, creator, managers, users):
        existing_board = Board.objects.filter(name='Доска разработки').first()
        if existing_board:
            existing_board.delete()

        board = Board.objects.create(
            name='Доска тестирования ML-модели',
            description='Доска для импортированных задач датасета и тестирования ML-модели',
            created_by=creator
        )

        open_status = BoardStatus.objects.create(
            board=board,
            name='Открытые',
            position=0
        )
        in_progress_status = BoardStatus.objects.create(
            board=board,
            name='В работе',
            position=1
        )
        in_progress_status = BoardStatus.objects.create(
            board=board,
            name='Тестируется',
            position=1
        )
        done_status = BoardStatus.objects.create(
            board=board,
            name='Готово',
            position=2
        )

        for manager in managers:
            BoardMember.objects.get_or_create(
                board=board,
                user=manager,
                defaults={'access': 'admin'}
            )

        for user in users:
            BoardMember.objects.get_or_create(
                board=board,
                user=user,
                defaults={'access': 'write'}
            )

        return board, {
            'open': open_status,
            'in_progress': in_progress_status,
            'done': done_status,
        }

    def read_unique_tasks(self, file_path):
        rows_by_issue = {}

        with open(file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')

            for row in reader:
                issue_id = str(row['issue_id']).strip()

                if issue_id not in rows_by_issue:
                    rows_by_issue[issue_id] = row

        return rows_by_issue

    def map_assignee(self, assignee_id, users):
        try:
            assignee_index = int(assignee_id)
        except:
            assignee_index = 1

        if assignee_index < 1:
            assignee_index = 1

        if assignee_index > len(users):
            assignee_index = ((assignee_index - 1) % len(users)) + 1

        return users[assignee_index - 1]

    def map_task_type(self, raw_value):
        value = str(raw_value).strip().lower()

        if value == 'ошибка':
            return 'bug'

        return 'task'

    def map_priority(self, raw_value):
        value = str(raw_value).strip().lower()

        if value in ['высокий', 'high', 'p1', 'p2']:
            return 'high'

        if value in ['средний', 'medium', 'p3']:
            return 'medium'

        if value in ['низкий', 'low', 'p4']:
            return 'low'

        return 'medium'

    def create_train_tasks(self, train_rows, board, done_status, managers, users):
        created_tasks = []

        for index, row in enumerate(train_rows):
            manager = managers[index % len(managers)]
            assignee = self.map_assignee(row.get('assignee_id'), users)

            task = Task.objects.create(
                title=row.get('summary', '').strip(),
                description=row.get('summary', '').strip(),
                board=board,
                status=done_status,
                author=manager,
                assignee=assignee,
                task_type=self.map_task_type(row.get('issue_type')),
                priority=self.map_priority(row.get('priority')),
                actual_time_spent=Decimal(str(row.get('actual_time_spent', '0')).replace(',', '.')),
                time_estimate=None,
            )

            HistoricalTaskData.objects.create(
                task=task,
                task_title=task.title,
                task_type=task.task_type,
                assignee_name=task.assignee.full_name if task.assignee else '',
                actual_time_spent=task.actual_time_spent,
            )

            created_tasks.append(task)

        return created_tasks

    def create_test_tasks(self, test_rows, board, open_status, managers, users):
        created_tasks = []

        for index, row in enumerate(test_rows):
            manager = managers[index % len(managers)]
            assignee = self.map_assignee(row.get('assignee_id'), users)

            task = Task.objects.create(
                title=row.get('summary', '').strip(),
                description=row.get('summary', '').strip(),
                board=board,
                status=open_status,
                author=manager,
                assignee=assignee,
                task_type=self.map_task_type(row.get('issue_type')),
                priority=self.map_priority(row.get('priority')),
                actual_time_spent=None,
                time_estimate=None,
            )

            created_tasks.append(task)

        return created_tasks