import random
from decimal import Decimal

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from boards.models import Board, BoardStatus, BoardMember
from tasks.models import Task
from predictions.models import HistoricalTaskData
from predictions.predictors import retrain_model_if_possible, create_or_update_prediction


class Command(BaseCommand):
    help = 'Импорт синтетического датасета, обучение модели и расчет прогнозов'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True)
        parser.add_argument('--test-size', type=int, default=200)
        parser.add_argument('--random-state', type=int, default=1)

    def handle(self, *args, **options):
        file_path = options['file']
        test_size = options['test_size']
        random_state = options['random_state']

        with transaction.atomic():
            managers = self.create_managers()
            employees = self.create_employees_from_excel(file_path)
            board, statuses = self.create_board(managers, employees)

            df = pd.read_excel(file_path, sheet_name='Tasks')
            df = df[['title', 'assignee', 'type', 'actual_time_spent']]
            df = df.dropna()

            rows = df.to_dict('records')

            rnd = random.Random(random_state)
            rnd.shuffle(rows)

            test_rows = rows[:test_size]
            train_rows = rows[test_size:]

            self.stdout.write(f'Обучающих задач: {len(train_rows)}')
            self.stdout.write(f'Тестовых задач: {len(test_rows)}')

            self.create_train_tasks(
                train_rows=train_rows,
                board=board,
                done_status=statuses['done'],
                managers=managers,
                employees=employees
            )

            model_trained = retrain_model_if_possible()

            if model_trained:
                self.stdout.write(self.style.SUCCESS('Модель успешно обучена'))
            else:
                self.stdout.write(self.style.ERROR('Модель не обучена: недостаточно данных'))
                return

            test_tasks = self.create_test_tasks(
                test_rows=test_rows,
                board=board,
                open_status=statuses['open'],
                managers=managers,
                employees=employees
            )

            for task in test_tasks:
                create_or_update_prediction(task)

            self.stdout.write(self.style.SUCCESS('Импорт синтетического датасета завершен'))
            self.stdout.write(f'Создано обучающих задач: {len(train_rows)}')
            self.stdout.write(f'Создано тестовых задач: {len(test_tasks)}')

    def create_managers(self):
        names = [
            'Алексей Смирнов',
            'Мария Иванова',
            'Дмитрий Кузнецов',
            'Екатерина Соколова',
        ]

        managers = []

        for index, name in enumerate(names, start=1):
            user, created = User.objects.get_or_create(
                email=f'synthetic_manager{index}@example.com',
                defaults={
                    'full_name': name,
                    'is_staff': True,
                    'is_admin': True,
                }
            )

            user.full_name = name
            user.is_staff = True
            user.is_admin = True
            user.set_password('admin')
            user.save()

            managers.append(user)

        return managers

    def create_employees_from_excel(self, file_path):
        df = pd.read_excel(file_path, sheet_name='Assignee')
        df = df.dropna(subset=['name'])

        employees = {}

        for index, row in df.iterrows():
            name = str(row['name']).strip()
            email = f'synthetic_user{index + 1}@example.com'

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': name,
                    'is_staff': False,
                    'is_admin': False,
                }
            )

            user.full_name = name
            user.is_staff = False
            user.is_admin = False
            user.set_password('admin')
            user.save()

            employees[name] = user

        return employees

    def create_board(self, managers, employees):
        old_board = Board.objects.filter(name='Синтетическая доска ML').first()
        if old_board:
            old_board.delete()

        board = Board.objects.create(
            name='Синтетическая доска ML',
            description='Доска для обучения и тестирования модели на синтетических данных',
            created_by=managers[0]
        )

        open_status = BoardStatus.objects.create(board=board, name='Открытые', position=0)
        progress_status = BoardStatus.objects.create(board=board, name='В работе', position=1)
        done_status = BoardStatus.objects.create(board=board, name='Готово', position=2)

        for manager in managers:
            BoardMember.objects.create(
                board=board,
                user=manager,
                access='admin'
            )

        for employee in employees.values():
            BoardMember.objects.create(
                board=board,
                user=employee,
                access='write'
            )

        return board, {
            'open': open_status,
            'progress': progress_status,
            'done': done_status,
        }

    def create_train_tasks(self, train_rows, board, done_status, managers, employees):
        for index, row in enumerate(train_rows):
            manager = managers[index % len(managers)]
            assignee = employees[str(row['assignee']).strip()]

            task = Task.objects.create(
                title=str(row['title']).strip(),
                description=str(row['title']).strip(),
                board=board,
                status=done_status,
                author=manager,
                assignee=assignee,
                task_type=str(row['type']).strip(),
                priority='medium',
                actual_time_spent=Decimal(str(row['actual_time_spent']).replace(',', '.')),
                time_estimate=None,
            )

            HistoricalTaskData.objects.create(
                task=task,
                task_title=task.title,
                task_type=task.task_type,
                assignee_name=task.assignee.full_name,
                actual_time_spent=task.actual_time_spent,
            )

    def create_test_tasks(self, test_rows, board, open_status, managers, employees):
        test_tasks = []

        for index, row in enumerate(test_rows):
            manager = managers[index % len(managers)]
            assignee = employees[str(row['assignee']).strip()]

            task = Task.objects.create(
                title=str(row['title']).strip(),
                description=f"Истинное время выполнения: {row['actual_time_spent']} ч.",
                board=board,
                status=open_status,
                author=manager,
                assignee=assignee,
                task_type=str(row['type']).strip(),
                priority='medium',
                actual_time_spent=None,
                time_estimate=None,
            )

            test_tasks.append(task)

        return test_tasks