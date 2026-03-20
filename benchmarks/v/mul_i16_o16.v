module mul_i16_o16 (a, b, r);
input [7:0] a, b;
output [15:0] r;


assign r = a * b;

endmodule 
