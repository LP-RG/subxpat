module mul_i192_o192 (a, b, r);
input [95:0] a,b;
output [191:0] r;

assign r = a * b;

endmodule
