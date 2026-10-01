module mul_i20_o20 (a, b, r);
input [63:0] a, b;
output [127:0] r;

assign r = a * b;

endmodule 
