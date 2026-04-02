module adder_i512_o257(a,b,r);
input [255:0] a,b;
output [256:0] r;

assign r = a+b;

endmodule
