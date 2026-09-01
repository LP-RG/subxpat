module mul_i20_o20 (a, b, r);
input [23:0] a, b;
output [47:0] r;


assign r = a * b;

endmodule 
