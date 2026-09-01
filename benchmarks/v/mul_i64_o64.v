module mul_i20_o20 (a, b, r);
input [31:0] a, b;
output [63:0] r;

assign r = a * b;

endmodule 
