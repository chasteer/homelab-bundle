# 🚀 Быстрая загрузка в GitHub

## 1. Создайте репозиторий на GitHub
- Перейдите на [github.com](https://github.com)
- Нажмите **"New repository"**
- Название: `homelab-bundle`
- Описание: `Полнофункциональный домашний сервер`
- Сделайте Public или Private
- НЕ инициализируйте с README (у нас уже есть)

## 2. Свяжите с локальным репозиторием
```bash
# Замените YOUR_USERNAME на ваше имя пользователя GitHub
git remote add origin https://github.com/YOUR_USERNAME/homelab-bundle.git

# Переименуйте ветку в main
git branch -M main

# Загрузите код
git push -u origin main
```

## 3. Готово! 🎉
Ваш Homelab Bundle теперь доступен на GitHub!

---

**Подробная инструкция**: [GITHUB_SETUP.md](GITHUB_SETUP.md)
