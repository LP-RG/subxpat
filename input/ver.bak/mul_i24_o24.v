module mul_i24_o24 (a, b, r);
input [11:0] a, b;
output [23:0] r;


assign r = a * b;

endmodule 
