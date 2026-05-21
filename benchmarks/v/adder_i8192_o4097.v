module adder_i8192_o4097(a,b,r);
input [4095:0] a,b;
output [4096:0] r;

assign r = a+b;

endmodule
