module mul_i20_o20 (a, b, r);
input [9:0] a, b;
output [19:0] r;


assign r = a * b;

endmodule 
