module mul_i26_o26 (a, b, r);
input [12:0] a,b;
output [25:0] r;

assign r = a * b;

endmodule
