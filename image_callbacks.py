import discord
import random
import utils
from view import ImageView

class ImageCallbackManager:
    """
    A utility class to manage common image generation callbacks
    to avoid repetitive code across different generation functions.
    """
    
    def __init__(self, server_ip, generation_params=None):
        """
        Initialize the callback manager
        
        Args:
            server_ip: The IP address of the ComfyUI server
            generation_params: Parameters used for image generation
        """
        self.server_ip = server_ip
        self.generation_params = generation_params or {}
        self.selected_image_info = {
            "index": 0,
            "path": None
        }
    
    def update_params(self, new_params):
        """Update generation parameters"""
        self.generation_params.update(new_params)
    
    async def on_image_change(self, index, file_path):
        """
        Callback for image selection change
        
        Args:
            index: Index of the selected image
            file_path: Path to the selected image file
            
        Returns:
            Selected image information
        """
        self.selected_image_info["index"] = index
        self.selected_image_info["path"] = file_path
        print(f"Image changed: index {index}, file path: {file_path}")
        return self.selected_image_info
    
    def create_retry_callback(self, generate_function, retry_message="Regenerating image..."):
        """
        Creates a retry callback function for the given generation function
        
        Args:
            generate_function: The async function to call for regeneration
            retry_message: The message to display when retrying
            
        Returns:
            A callback function for retry button
        """
        async def on_retry_clicked(interaction):
            print("Retry button clicked, regenerating image")
            
            # Generate new seed(s)
            if 'needs_multiple_seeds' in self.generation_params and self.generation_params['needs_multiple_seeds']:
                seed_count = self.generation_params.get('seed_count', 4)
                new_seeds = [random.randint(1, 2147483647) for _ in range(seed_count)]
                seed_message = "new seeds"
            else:
                new_seeds = random.randint(1, 2147483647)
                seed_message = f"new seed: {new_seeds}"
            
            # Create retry message
            retry_embed = utils.set_embed(
                "Image Regeneration Started", 
                f"{retry_message} Using {seed_message}", 
                discord.Color.blue()
            )
            await interaction.followup.send(embed=retry_embed, ephemeral=True)
            
            # Call the provided function with new seeds
            if 'needs_multiple_seeds' in self.generation_params and self.generation_params['needs_multiple_seeds']:
                result = await generate_function(interaction, self.generation_params, new_seeds)
            else:
                result = await generate_function(interaction, self.generation_params, new_seeds)
                
            return result
            
        return on_retry_clicked
    
    def create_upscale_callback(self, upscale_function):
        """
        Creates an upscale callback function
        
        Args:
            upscale_function: The async function to call for upscaling
            
        Returns:
            A callback function for upscale button
        """
        async def on_upscale_clicked(interaction, selected_image_path):
            print(f"Upscale button clicked, upscaling image: {selected_image_path}")
            
            prompt_text = self.generation_params.get('prompt_text', '')
            await upscale_function(interaction, selected_image_path, prompt_text)
            
        return on_upscale_clicked
    
    def create_next_callback(self, next_function):
        """
        Creates a next stage callback function
        
        Args:
            next_function: The async function to call for the next stage
            
        Returns:
            A callback function for next button
        """
        async def on_next_clicked(interaction, selected_image_path):
            print(f"Next button clicked, moving to next stage with image: {selected_image_path}")
            
            # Call the next stage function with the selected image path
            await next_function(
                interaction,
                **self.generation_params,
                selected_image_path=selected_image_path
            )
            
        return on_next_clicked
    
    def create_view(self, image_files, image_paths, description, 
                    retry_function=None, upscale_function=None, next_function=None,
                    is_next_button_visible=True):
        """
        Creates an ImageView with appropriate callbacks
        
        Args:
            image_files: List of image file objects
            image_paths: Dictionary of image paths
            description: Description for the view
            retry_function: Function to generate retry callback
            upscale_function: Function to generate upscale callback
            next_function: Function to generate next callback
            is_next_button_visible: Whether the next button should be visible
            
        Returns:
            Configured ImageView object
        """
        on_retry_click = self.create_retry_callback(retry_function) if retry_function else None
        on_upscale_click = self.create_upscale_callback(upscale_function) if upscale_function else None
        on_next_click = self.create_next_callback(next_function) if next_function else None
        
        return ImageView(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            on_image_change=self.on_image_change,
            on_retry_click=on_retry_click,
            on_upscale_click=on_upscale_click,
            on_next_click=on_next_click,
            is_next_button_visible=is_next_button_visible
        ) 