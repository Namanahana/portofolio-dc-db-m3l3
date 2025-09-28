import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
manager = DB_Manager(DATABASE)

# Fungsi ini akan berjalan jika bot sudah di run
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

# Fungsi ini berguna untuk membuat bot mengirim pesan
@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Halo! Saya adalah bot manajer proyek\nSaya akan membantu kamu menyimpan proyek dan informasi tentangnya!)")
    await info(ctx)

# Fungsi ini untuk memeriksa perintah yang bisa digunakan
@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Berikut adalah perintah yang dapat membantu kamu:

!new_project - gunakan untuk menambahkan proyek baru
!projects - gunakan untuk menampilkan semua proyek
!update_projects - gunakan untuk mengubah data proyek
!skills - gunakan untuk menghubungkan keterampilan ke proyek
!delete - gunakan untuk menghapus proyek

Kamu juga dapat memasukkan nama proyek untuk mengetahui informasi tentangnya!""")

# Fungsi ini untuk membuat project baru dengan menyertakan nama, link, & status project
@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Masukkan nama proyek:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)
    data = [ctx.author.id, name.content]

    await ctx.send("Masukkan deskripsi proyek")
    deskripsi = await bot.wait_for('message', check=check)
    data.append(deskripsi.content)

    await ctx.send("Masukkan link proyek")
    link = await bot.wait_for('message', check=check)
    data.append(link.content)

    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Masukkan status proyek saat ini", delete_after=60.0)
    await ctx.send("\n".join(statuses), delete_after=60.0)
    
    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("Kamu memilih status yang tidak ada dalam daftar, silakan coba lagi!)", delete_after=60.0)
        return

    status_id = manager.get_status_id(status.content)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    await ctx.send("Proyek telah disimpan")

# Fungsi ini untuk memeriksa project apa saja yang sudah dibuat
@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        await ctx.send(text)
    else:
        await ctx.send('Kamu belum memiliki proyek!\nKamu dapat menambahkannya menggunakan perintah !new_project')

# Fungsi ini berguna untuk menambahkan keterampilan yang dimiliki oleh project
@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send('Pilih proyek yang ingin kamu tambahkan keterampilan')
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Kamu tidak memiliki proyek tersebut, silakan coba lagi!) Pilih proyek yang ingin kamu tambahkan keterampilan')
            return

        skills = [x[1] for x in manager.get_skills()]
        await ctx.send('Pilih keterampilan')
        await ctx.send("\n".join(skills))

        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills:
            await ctx.send('Sepertinya kamu memilih keterampilan yang tidak ada dalam daftar, silakan coba lagi!) Pilih keterampilan')
            return

        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'Keterampilan {skill.content} telah ditambahkan ke proyek {project_name.content}')
    else:
        await ctx.send('Kamu belum memiliki proyek!\nKamu dapat menambahkannya menggunakan perintah !new_project')

# Fungsi ini untuk menghapus project
@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Pilih proyek yang ingin kamu hapus")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Kamu tidak memiliki proyek tersebut, silakan coba lagi!')
            return

        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'Proyek {project_name.content} telah dihapus!')
    else:
        await ctx.send('Kamu belum memiliki proyek!\nKamu dapat menambahkannya menggunakan perintah !new_project')

# Fungsi ini untuk memperbarui data yang ada di dalam project
@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Pilih proyek yang ingin kamu ubah")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send("Ada yang salah! Silakan pilih proyek yang ingin kamu ubah lagi:")
            return

        await ctx.send("Pilih apa yang ingin kamu ubah dalam proyek")
        attributes = {'Nama proyek': 'project_name', 'Deskripsi': 'description', 'Link': 'url', 'Status': 'status_id'}
        await ctx.send("\n".join(attributes.keys()))

        attribute = await bot.wait_for('message', check=check)
        if attribute.content not in attributes:
            await ctx.send("Sepertinya kamu membuat kesalahan, silakan coba lagi!")
            return

        if attribute.content == 'Status':
            statuses = manager.get_statuses()
            await ctx.send("Pilih status baru untuk proyek")
            await ctx.send("\n".join([x[0] for x in statuses]))
            update_info = await bot.wait_for('message', check=check)
            if update_info.content not in [x[0] for x in statuses]:
                await ctx.send("Status yang dipilih tidak valid, silakan coba lagi!")
                return
            update_info = manager.get_status_id(update_info.content)
        else:
            await ctx.send(f"Masukkan nilai baru untuk {attribute.content}")
            update_info = await bot.wait_for('message', check=check)
            update_info = update_info.content

        manager.update_projects(attributes[attribute.content], (update_info, project_name.content, user_id))
        await ctx.send("Selesai! Pembaruan telah dilakukan!")
    else:
        await ctx.send('Kamu belum memiliki proyek!\nKamu dapat menambahkannya menggunakan perintah !new_project')

bot.run(TOKEN)
