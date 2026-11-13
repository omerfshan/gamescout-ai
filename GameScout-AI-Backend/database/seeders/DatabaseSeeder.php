<?php
declare(strict_types=1);
namespace Database\Seeders;
use App\Models\User;
use Illuminate\Database\Seeder;
final class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $rawEmail = trim((string) env('DEMO_USER_EMAIL', 'demo@gamescout.local'));
        $email = $rawEmail !== '' ? strtolower($rawEmail) : 'demo@gamescout.local';
        $rawPassword = trim((string) env('DEMO_USER_PASSWORD', 'demo-scout-2026'));
        $password = ($rawPassword === '' || $rawPassword === 'REPLACE_LOCALLY') ? 'demo-scout-2026' : $rawPassword;
        User::query()->updateOrCreate(
            ['email' => $email],
            [
                'name' => 'Demo Araştırmacı',
                'password' => $password,
            ]
        );
    }
}
