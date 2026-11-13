export type Platform = 'android' | 'ios';
export type PlatformFilter = Platform | 'all';
export type DeveloperProfile = 'indie' | 'small_team' | 'unknown';

export interface Game {
  game_id: string;
  platform: Platform;
  external_app_id: string;
  title: string;
  developer_profile: DeveloperProfile;
  normalized_genres: string[];
  source_record_id: string;
}

export interface GamesResponse {
  data: Game[];
  meta: {
    data_origin: 'synthetic_demo';
    demo_label: string;
    count: number;
  };
}
