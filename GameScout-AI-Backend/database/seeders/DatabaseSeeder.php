<?php
declare(strict_types=1);
namespace Database\Seeders;
use App\Models\User;
use Illuminate\Database\Seeder;
final class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        User::query()->updateOrCreate(
            ['email' => 'admin@gamescout.ai'],
            [
                'name' => 'GameScout Araştırmacı',
                'password' => 'gamescout2026',
            ]
        );
        User::query()->updateOrCreate(
            ['email' => 'demo@gamescout.local'],
            [
                'name' => 'GameScout Araştırmacı',
                'password' => 'demo-scout-2026',
            ]
        );
    }
}
