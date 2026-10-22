# Builds a resource pack that puts the 1.2.5 terrain.png textures on the modern block texture names,
# so BlueMap (and a modern client) shows YAM the way it looked in 2012.
# python build_pack.py <terrain.png> <out_dir>
import os, sys, json
from PIL import Image

# modern texture name (assets/minecraft/textures/block/<name>.png) -> 1.2.5 terrain.png tile index
TEX = {
    'grass_block_top': 0, 'stone': 1, 'dirt': 2, 'grass_block_side': 3, 'oak_planks': 4,
    'smooth_stone_slab_side': 5, 'smooth_stone': 6, 'bricks': 7, 'tnt_side': 8, 'tnt_top': 9, 'tnt_bottom': 10,
    'cobweb': 11, 'poppy': 12, 'dandelion': 13, 'oak_sapling': 15,
    'cobblestone': 16, 'bedrock': 17, 'sand': 18, 'gravel': 19, 'oak_log': 20, 'oak_log_top': 21,
    'iron_block': 22, 'gold_block': 23, 'diamond_block': 24, 'red_mushroom': 28, 'brown_mushroom': 29,
    'jungle_sapling': 30,
    'gold_ore': 32, 'iron_ore': 33, 'coal_ore': 34, 'bookshelf': 35, 'mossy_cobblestone': 36, 'obsidian': 37,
    'grass_block_side_overlay': 38, 'short_grass': 39, 'crafting_table_top': 43, 'furnace_front': 44,
    'furnace_side': 45, 'dispenser_front': 46,
    'sponge': 48, 'glass': 49, 'diamond_ore': 50, 'redstone_ore': 51, 'oak_leaves': 52, 'stone_bricks': 54,
    'dead_bush': 55, 'fern': 56, 'crafting_table_side': 59, 'crafting_table_front': 60,
    'furnace_front_on': 61, 'furnace_top': 62, 'spruce_sapling': 63,
    'white_wool': 64, 'spawner': 65, 'snow': 66, 'ice': 67, 'grass_block_snow': 68, 'cactus_top': 69,
    'cactus_side': 70, 'cactus_bottom': 71, 'clay': 72, 'sugar_cane': 73, 'jukebox_side': 74, 'jukebox_top': 75,
    'lily_pad': 76, 'mycelium_side': 77, 'mycelium_top': 78, 'birch_sapling': 79,
    'torch': 80, 'oak_door_top': 81, 'iron_door_top': 82, 'ladder': 83, 'oak_trapdoor': 84, 'iron_bars': 85,
    'farmland_moist': 86, 'farmland': 87,
    'wheat_stage0': 88, 'wheat_stage1': 89, 'wheat_stage2': 90, 'wheat_stage3': 91, 'wheat_stage4': 92,
    'wheat_stage5': 93, 'wheat_stage6': 94, 'wheat_stage7': 95,
    'lever': 96, 'oak_door_bottom': 97, 'iron_door_bottom': 98, 'redstone_torch': 99,
    'mossy_stone_bricks': 100, 'cracked_stone_bricks': 101, 'pumpkin_top': 102, 'netherrack': 103,
    'soul_sand': 104, 'glowstone': 105, 'piston_top_sticky': 106, 'piston_top': 107, 'piston_side': 108,
    'piston_bottom': 109, 'piston_inner': 110, 'pumpkin_stem': 111,
    'rail_corner': 112, 'black_wool': 113, 'gray_wool': 114, 'redstone_torch_off': 115, 'spruce_log': 116,
    'birch_log': 117, 'pumpkin_side': 118, 'carved_pumpkin': 119, 'jack_o_lantern': 120, 'cake_top': 121,
    'cake_side': 122, 'cake_inner': 123, 'cake_bottom': 124, 'red_mushroom_block': 125,
    'brown_mushroom_block': 126, 'attached_pumpkin_stem': 127,
    'rail': 128, 'red_wool': 129, 'pink_wool': 130, 'repeater': 131, 'spruce_leaves': 132,
    'melon_side': 136, 'melon_top': 137, 'cauldron_top': 138, 'cauldron_inner': 139,
    'mushroom_stem': 141, 'mushroom_block_inside': 142, 'vine': 143,
    'lapis_block': 144, 'green_wool': 145, 'lime_wool': 146, 'repeater_on': 147, 'glass_pane_top': 148,
    'jungle_log': 153, 'cauldron_side': 154, 'cauldron_bottom': 155, 'brewing_stand_base': 156,
    'brewing_stand': 157, 'end_portal_frame_top': 158, 'end_portal_frame_side': 159,
    'lapis_ore': 160, 'brown_wool': 161, 'yellow_wool': 162, 'powered_rail': 163,
    'redstone_dust_dot': 164, 'redstone_dust_line0': 165, 'redstone_dust_line1': 165,
    'enchanting_table_top': 166, 'dragon_egg': 167,
    'sandstone_top': 176, 'blue_wool': 177, 'light_blue_wool': 178, 'powered_rail_on': 179,
    'enchanting_table_side': 182, 'enchanting_table_bottom': 183,
    'sandstone': 192, 'purple_wool': 193, 'magenta_wool': 194, 'detector_rail': 195, 'jungle_leaves': 196,
    'spruce_planks': 198, 'jungle_planks': 199,
    'sandstone_bottom': 208, 'cyan_wool': 209, 'orange_wool': 210, 'redstone_lamp': 211, 'redstone_lamp_on': 212,
    'chiseled_stone_bricks': 213, 'birch_planks': 214,
    'nether_bricks': 224, 'light_gray_wool': 225, 'nether_wart_stage0': 226, 'nether_wart_stage1': 227,
    'nether_wart_stage2': 228, 'chiseled_sandstone': 229, 'cut_sandstone': 230,
    'end_stone': 175, 'birch_leaves': 52,
    'spruce_log_top': 21, 'birch_log_top': 21, 'jungle_log_top': 21,
}
# 1.2.5 drew water and lava procedurally; use the still tiles from the atlas as flat stand-ins
# Water is left modern: the modern texture is grey and tinted, the 1.2.5 tile is already blue.
STILL = {'lava_still': 237, 'lava_flow': 238}


def main():
    t = Image.open(sys.argv[1]).convert('RGBA'); out = sys.argv[2]
    d = os.path.join(out, 'assets', 'minecraft', 'textures', 'block'); os.makedirs(d, exist_ok=True)
    tile = lambda i: t.crop((i % 16 * 16, i // 16 * 16, i % 16 * 16 + 16, i // 16 * 16 + 16))
    for name, i in {**TEX, **STILL}.items():
        tile(i).save(os.path.join(d, name + '.png'))
    if len(sys.argv) > 3:  # 1.2.5 item/sign.png has the same 64x32 layout as the modern oak sign entity texture
        e = os.path.join(out, 'assets', 'minecraft', 'textures', 'entity', 'signs'); os.makedirs(e, exist_ok=True)
        Image.open(sys.argv[3]).convert('RGBA').save(os.path.join(e, 'oak.png'))
    json.dump({'pack': {'pack_format': 22, 'description': 'You Are Minecraft 2012 look (1.2.5 terrain)'}},
              open(os.path.join(out, 'pack.mcmeta'), 'w'))
    print(len(TEX) + len(STILL), 'textures')


main()
